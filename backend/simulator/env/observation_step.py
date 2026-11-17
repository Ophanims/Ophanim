import math
import numpy as np
import logging
import os
from simulator.schemas.project import Project
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.schemas.task import Task
import gymnasium as gym
from gymnasium import spaces
from typing import List
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.env.core.constraints import all_tasks_completed, all_tasks_overtimed, any_satellite_depleted
from simulator.config import ALL_TASK_COMPLETION_REWARD, ENERGY_DROWN_PENALTY, LAYER_OUTPUT_DATA_SIZE, IDLE_PENALTY, MAX_NUM_TASKS, DEBUG, LOG_OUTPUT
from simulator.env.core.entity_col import EntityCol
from simulator.env.core.task_manager import TaskManager
from simulator.env.vars.request import CompReq, TransReq
from simulator.env.core.formulation import compute_delay_penalty, compute_energy_penalty, reward_function
from simulator.env.core.operation import do_computing, do_energy_updating, do_transferring
from simulator.env.core.observation import get_obs
from datetime import datetime, timedelta, timezone
from simulator.entities.earth_entity import EarthEntity
from simulator.entities.roi_entity import ROIEntity
from simulator.entities.sun_entity import SunEntity
from simulator.services.network_service import Network
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.entities.station_entity import StationEntity
from simulator.schemas.project import Project


class ObservationStep:

    def step(self, actions):
        print(f"Step {self.frame_counter}: actions={actions}")
        # 初始化数值
        self.state_manager.clear_progress_counters()
        self.decision_manager.reset()
        action_reward = 0.0
        trans_reqs: List[TransReq] = []
        comp_reqs: List[CompReq] = []

        terminated, truncated = False, False
        terminated_reason, truncated_reason = "None", "None"

        # 获取当前任务和节点状态
        # nodes, edges = self.EG.get_nodes(), self.EG.get_edges()
        nodes = self.sat
        edges = self.net.compute_isl_links_at(self.period_counter, self.slot_counter)

        all_tasks = self.task_manager.get_tasks()
        tasks = self.task_manager.get_tasks_at(step=self.frame_counter)
        n_tasks = len(tasks)

        # 获取有效动作
        valid_actions = list(actions)[:n_tasks]

        # 初始化状态管理器和决策管理器的活跃任务数
        self.state_manager.update(n_tasks)
        self.decision_manager.update(n_tasks)

        assert len(valid_actions) == n_tasks

        for task, act in zip(tasks, valid_actions):
            if DEBUG and task.id == 0:
                state0 = self.task_manager.task_state(task)
                allowed0 = self.get_allowed_actions(task)
                self.logger.debug(
                    f"[Task0] pre-validate: acted={task.acted} state={state0} allowed={sorted(list(allowed0))} "
                    f"workload_done={task.workload_done} data_sent={task.data_sent} t_start={task.t_start} t_end={task.t_end}"
                )

            if task.is_done:
                continue

            p, o = task.plane_at, task.order_at

            node = next((s for s in self.sat if s.plane == p and s.order == o), None)
            if node is None:
                continue

            # if node.battery_ratio <= 0:
            #     task.t_end += 1
            #     continue

            # validate action; validate_action returns (valid: bool, penalty: float, truncated: bool, reason: str)
            is_valid, penalty, is_truncated, truncated_reason_local = self.validate_action(task, act)
            if not is_valid:
                # apply penalty for invalid action
                action_reward += penalty
                if DEBUG:
                    self.logger.debug(f"[InvalidAction] Task {task.id} act={act} state_penalty={penalty} reason={truncated_reason_local}")

                # Remap to a legal fallback to keep learning signal dense
                allowed = self.get_allowed_actions(task)

                # Prefer compute (5) if allowed and not occupied
                remapped_act = None
                if 5 in allowed and not self.decision_manager.is_po_occupied(p=p, o=o):
                    if task.acted in [0, 1, 2, 3, 4]:
                        action_reward += FIRST_COMPUTE_BONUS
                    remapped_act = 5
                else:
                    # Fallback to no-op if compute isn't available; this stabilizes learning
                    action_reward += IDLE_PENALTY
                    remapped_act = 0

                # task.t_end += 1
                # task.acted = remapped_act
                act = remapped_act
                # Reset repeat counter when not moving
                if remapped_act not in [1, 2, 3, 4]:
                    self.repeat_move_counts[task.id] = 0
                # continue

            # action is valid -> apply effects
            if act == 0:
                # 统计连续 no-op
                self.idle_counts[task.id] = self.idle_counts.get(task.id, 0) + 1
                # 若允许计算且当前位置未被占用，防止长期空转：转为计算
                allowed = self.get_allowed_actions(task)
                if 5 in allowed and not self.decision_manager.is_po_occupied(p=p, o=o):
                    # 触发“从空转到计算”的正向激励
                    action_reward += FIRST_COMPUTE_BONUS
                    self.decision_manager.write_pi(p=p, o=o, m=task.id, value=True)
                    node.is_processing = True
                    comp_reqs.append(
                        CompReq(
                            task_id=task.id,
                            node_id=(p, o),
                            layer_id=task.layer_id,
                        )
                    )
                    act = 5
                    # 重置空转计数
                    self.idle_counts[task.id] = 0
                else:
                    action_reward += IDLE_PENALTY

            elif act in [1, 2, 3, 4]:
                # 基础移动惩罚（降低无意义移动的吸引力）
                # action_reward += BASE_MOVE_PENALTY

                # 连续移动惩罚逻辑
                prev_act = task.acted
                if prev_act in [1,2,3,4]:
                    self.repeat_move_counts[task.id] = self.repeat_move_counts.get(task.id, 0) + 1
                else:
                    self.repeat_move_counts[task.id] = 1

                # 移动时重置空转计数
                self.idle_counts[task.id] = 0

                if self.repeat_move_counts[task.id] > 3:
                    excess = self.repeat_move_counts[task.id] - 3
                    # penalty = REPEAT_MOVE_PENALTY_BASE * excess
                    # Cap the per-step repeat move penalty to avoid runaway negatives
                    # if penalty < REPEAT_MOVE_PENALTY_CAP:
                    #     penalty = REPEAT_MOVE_PENALTY_CAP
                    action_reward += penalty
                    if DEBUG:
                        self.logger.debug(f"[Penalty] Task {task.id} repeat move count={self.repeat_move_counts[task.id]} penalty={penalty:.3f}")

                    # 防止“永远绕圈”：若可计算且未占用，强制改为计算
                    allowed = self.get_allowed_actions(task)
                    if 5 in allowed and not self.decision_manager.is_po_occupied(p=p, o=o):
                        self.decision_manager.write_pi(p=p, o=o, m=task.id, value=True)
                        node.is_processing = True
                        if node.is_charging:
                            self.at_sunlit_sat += 1
                        else:
                            self.at_dark_sat += 1
                        comp_reqs.append(
                            CompReq(
                                task_id=task.id,
                                node_id=(p, o),
                                layer_id=task.layer_id,
                            )
                        )
                        # 从移动切到计算，给予一次性奖励
                        action_reward += FIRST_COMPUTE_BONUS
                        act = 5
                        # 重置重复移动计数，防止再次触发
                        self.repeat_move_counts[task.id] = 0

                # movement actions
                if act == 1:
                    dst = ((p + 1) % self.entity_collection.number_of_planes, o)
                elif act == 2:
                    dst = ((p - 1) % self.entity_collection.number_of_planes, o)
                elif act == 3:
                    dst = (p, (o + 1) % self.entity_collection.number_of_sat_per_planes)
                else:
                    dst = (p, (o - 1) % self.entity_collection.number_of_sat_per_planes)

                if ((p, o), dst) in self.entity_collection.edges_dict:
                    # only record legal link usage into DM
                    self.decision_manager.write_rho(u=(p, o), v=dst, m=task.id, value=True)
                    data_bits = LAYER_OUTPUT_DATA_SIZE[task.layer_id]
                    node.is_communicating_isl = True
                    trans_reqs.append(
                        TransReq(
                            task_id=task.id,
                            src=(p, o),
                            dst=dst,
                        )
                    )
                else:
                    # illegal edge: apply penalty, and try to remap to compute if allowed
                    # action_reward += WRONG_EDGE_PENALTY
                    # 重置该任务的重复移动计数，避免惩罚爆炸
                    self.repeat_move_counts[task.id] = 0
                    # if DEBUG:
                        # self.logger.debug(f"[IllegalLink] Task {task.id} src={(p,o)} dst={dst} penalty={WRONG_EDGE_PENALTY}")
                    allowed = self.get_allowed_actions(task)
                    if 5 in allowed and not self.decision_manager.is_po_occupied(p=p, o=o):
                        # workload = LAYER_PROCESS_STEP_COST[task.layer_id]
                        self.decision_manager.write_pi(p=p, o=o, m=task.id, value=True)
                        node.is_processing = True
                        comp_reqs.append(
                            CompReq(
                                task_id=task.id,
                                node_id=(p, o),
                                layer_id=task.layer_id,
                            )
                        )
                        if task.acted in [0, 1, 2, 3, 4]:
                            action_reward += FIRST_COMPUTE_BONUS
                        # mark effective action as compute for bookkeeping
                        act = 5
                    else:
                        # fallback to no-op once for stability (avoid stacking penalties)
                        act = 0
                        action_reward += IDLE_PENALTY
                    # proceed without 'continue' so that acted/t_end update below applies

            elif act == 5:
                # 使用 DecisionManager 的占用检查（按步重置，更适合并发约束）
                is_occupied = self.decision_manager.is_po_occupied(p=p, o=o)
                if not is_occupied:
                    # workload = LAYER_PROCESS_STEP_COST[task.layer_id]
                    self.decision_manager.write_pi(p=p, o=o, m=task.id, value=True)
                    node.is_processing = True
                    comp_reqs.append(
                        CompReq(
                            task_id=task.id,
                            node_id=(p, o),
                            layer_id=task.layer_id,
                        )
                    )
                    # 从 idle 或 transferring 切到 compute 时给一次额外奖励
                    if task.acted in [0,1,2,3,4]:
                        action_reward += FIRST_COMPUTE_BONUS
                    # else:
                    #     # 连续计算时的持续奖励，鼓励坚持计算
                    #     action_reward += SUSTAINED_COMPUTE_BONUS
                else:
                    action_reward += IDLE_PENALTY

            task.t_end += 1
            task.acted = act

            # 非移动动作重置计数
            if act not in [1,2,3,4]:
                self.repeat_move_counts[task.id] = 0

        # 执行传输与计算
        action_reward += do_transferring(slot=self.slot_in_num, tasks=tasks, trans_reqs=trans_reqs, sm=self.state_manager, dm=self.decision_manager)
        action_reward += do_computing(slot=self.slot_in_num, tasks=tasks, comp_reqs=comp_reqs, sm=self.state_manager, dm=self.decision_manager)
        do_energy_updating(slot=self.slot_in_num, nodes=nodes, sm=self.state_manager)

        # 计算目标向导奖励（与动作奖励合并前先计算，以便最终汇总）
        aim_reward = reward_function(delay_penalty=compute_delay_penalty(self.slot_in_num, tasks), energy_penalty=compute_energy_penalty(nodes))

        # 终止/截断判定
        if all_tasks_completed(all_tasks):
            action_reward += ALL_TASK_COMPLETION_REWARD
            terminated = True
            terminated_reason = "all_tasks_completed"

        elif any_satellite_depleted(nodes):
            action_reward += ENERGY_DROWN_PENALTY
            terminated = True
            terminated_reason = "satellite_energy_depleted"

        # if all_tasks_overtimed(tasks, self.slot_in_num):
        #     action_reward += OVERTIME_PENALTY
        #     truncated = True
        #     truncated_reason = "all_tasks_overtimed"

        # elif any_illegal_link(self.SM, self.DM):
        #     action_reward += WRONG_EDGE_PENALTY
        #     truncated = True
        #     truncated_reason = "any_illegal_link"

        # 终端/截断调整后，合并最终奖励
        reward = action_reward + aim_reward
        if DEBUG:
            self.logger.debug(f"[StepSummary] frame={self.frame_counter} action_reward={action_reward:.3f} aim_reward={aim_reward:.3f} total={reward:.3f}")
            if self.repeat_move_counts:
                self.logger.debug(f"[RepeatMoves] {self.repeat_move_counts}")

        # 产出观测和可序列化的 info
        obs, dbg_info = get_obs(sm=self.state_manager, dm=self.decision_manager, tm=self.task_manager, step=self.frame_counter)

        # 使用 dict 替代 Info 对象，确保可序列化返回
        info_serial = {
            "num_nodes": len(nodes),
            "num_edges": len(edges),
            "num_tasks": n_tasks,
            "reward": float(reward),
            "truncated_reason": truncated_reason,
            "terminated_reason": terminated_reason,
            "is_truncated": bool(truncated),
            "is_terminated": bool(terminated),
        }

        self.frame_counter += 1
        if self.slot_counter < self.max_slot_number - 1:
            self.time_recorder = self.time_recorder + self.slot
            self.slot_counter += 1
        else:
            self.slot_counter = 0
            next_period = self.period_counter + 1
            # If next period would exceed available timeline, truncate episode
            if next_period >= self.max_period_numbers:
                truncated = True
                truncated_reason = "max_period_reached"
                # clamp to last available period index and keep current time
                self.period_counter = self.max_period_numbers - 1
                # ensure time_recorder stays within bounds
                if self.datetime_list:
                    self.time_recorder = self.datetime_list[self.period_counter]
            else:
                self.period_counter = next_period
                # update time to the new period boundary
                self.time_recorder = self.datetime_list[self.period_counter]
                self.period_update()

        return self._align_obs(obs), reward, terminated, truncated, info_serial

