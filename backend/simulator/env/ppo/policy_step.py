import math
import numpy as np
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.schemas.task import Task
from simulator.env.core.logger import SystemLogger
from simulator.schemas.project import Project
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, List, Tuple
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.env.core.constraints import all_tasks_completed, all_tasks_overtimed, any_satellite_depleted, any_tasks_overtimed
from simulator.config import ALL_TASK_COMPLETION_REWARD, COMP_PENALTY, ENERGY_DROWN_PENALTY, IDLE_PENALTY, TRAN_PENALTY
from simulator.env.core.entity_col import EntityCol
from simulator.env.core.task_manager import TaskManager
from simulator.env.vars.request import CompReq, TransReq
from simulator.env.core.formulation import compute_delay_penalty, compute_energy_penalty, reward_function
from simulator.env.core.operation import do_computing, do_energy_dynamic, do_energy_static, do_energy_updating, do_transferring
from simulator.env.core.observation import get_obs, get_obs_space_shape
from datetime import datetime, timedelta, timezone
from simulator.entities.earth_entity import EarthEntity
from simulator.entities.roi_entity import ROIEntity
from simulator.entities.sun_entity import SunEntity
from simulator.services.network_service import LinkSnapshot, Network
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.entities.station_entity import StationEntity


class PolicyStep:

    def step(self, action):
        act = int(action)

        # 初始化数值
        step_reward = 0.0

        terminated, truncated = False, False
        terminated_reason, truncated_reason = "None", "None"

        if len(self.current_tasks) == 0:
            # 无任务时也推进能量与时间，同时产出固定形状观测（包含 38 维 task_stats，全 0 表示无任务）
            obs, dbg_info = get_obs(sm=self.state_manager, dm=self.decision_manager, step=self.frame_counter)
            info_serial = {
                "reward": step_reward,
                "truncated_reason": "None",
                "terminated_reason": "None",
                "is_truncated": False,
                "is_terminated": False,
                "action_mask": np.ones(6, dtype=np.int8),  # 无任务时全允许
            }
            # 时间推进
            self.discrete_time_update()
            return obs, step_reward, False, False, info_serial

        # Update state manager with current tasks, nodes, and edges
        # Note: StateManager.update does not accept a 'slot' parameter
        self.state_manager.update(tasks=self.current_tasks, all_nodes=self.current_nodes, all_edges=self.current_edges)
        task = self.current_tasks[self.current_task_idx]
        self.logger.info(f"Step {self.frame_counter}: task={self.current_task_idx}/{len(self.current_tasks)} acted={task.acted} action={act} in [{self.get_allowed_actions(task)}]")

        p, o = task.plane_at, task.order_at
        node = next((s for s in self.sat if s.plane == p and s.order == o), None)

        com_req = next((r for r in self.comp_reqs if r.task.id == task.id), None)
        tr_req = next((r for r in self.trans_reqs if r.task.id == task.id), None)

        is_no_energy = node.battery_ratio <= 0.0 if node else True

        # 行为有效性校验（防止处理中任务被打断或非法移动）
        # is_valid = self.validate_action(task, act)
        # if not is_valid:
        #     self.LG.warning(f"Invalid action {act} taken")

        if not com_req and not tr_req and not is_no_energy:
            # 强化奖励设计
            if act == 0:
                # self.idle_counts[task.id] = self.idle_counts.get(task.id, 0) + 1
                # idle_counts = self.idle_counts[task.id]
                # idle_factor = min(3, idle_counts)  # 空转惩罚最多放大到 3 倍
                # step_reward += idle_factor * NO_ACTION_PENALTY
                step_reward += IDLE_PENALTY

            elif act in [1, 2, 3, 4]:
                # prev_act = task.acted
                # if prev_act == act:
                #     self.repeat_move_counts[task.id] = self.repeat_move_counts.get(task.id, 0) + 1
                # else:
                #     self.repeat_move_counts[task.id] = 0

                # repeat_count = self.repeat_move_counts[task.id]
                # move_factor = min((3 - repeat_count), 0)
                # step_reward += max(move_factor * 0.1, -1)

                # movement actions
                if act == 1:
                    dst = ((p + 1) % self.entity_collection.number_of_planes, o)
                elif act == 2:
                    dst = ((p - 1) % self.entity_collection.number_of_planes, o)
                elif act == 3:
                    dst = (p, (o + 1) % self.entity_collection.number_of_sat_per_planes)
                else:
                    dst = (p, (o - 1) % self.entity_collection.number_of_sat_per_planes)
                dst_node = next((s for s in self.sat if s.plane == dst[0] and s.order == dst[1]), None)
                if ((p, o), dst) in self.entity_collection.edges_dict:
                    tr_req = TransReq(
                        task=task,
                        src=node,
                        dst=dst_node,
                    )
                    self.trans_reqs.append(tr_req)
                # else:
                #     action_reward += WRONG_EDGE_PENALTY
            elif act == 5:
                is_occupied = any(c.node.id == node.id for c in self.comp_reqs)
                if not is_occupied:
                    # 只有从“动/空转”切到可用的计算节点时，给一次小 bonus
                    # if self.repeat_move_counts.get(task.id, 0) >= 1 or self.idle_counts.get(task.id, 0) >= 1:
                    #     self.repeat_move_counts[task.id] = 0
                    #     self.idle_counts[task.id] = 0
                    #     step_reward += FIRST_COMPUTE_BONUS

                    com_req = CompReq(task=task, node=node)
                    self.comp_reqs.append(com_req)
            task.acted = act

        # 执行传输与计算（仅对当前任务）
        if tr_req:
            step_reward += do_transferring(
                slot=self.slot_in_num,
                sm=self.state_manager,
                dm=self.decision_manager,
                req=tr_req,
                reqs=self.trans_reqs,
            )
            # 成功进行传输则视为非重复移动情形，重置移动计数
            # self.repeat_move_counts[task.id] = 0

        if com_req:
            if node.is_charging:
                self.at_sunlit_sat += 1
            else:
                self.at_dark_sat += 1
            step_reward += do_computing(
                slot=self.slot_in_num,
                sm=self.state_manager,
                dm=self.decision_manager,
                req=com_req,
                reqs=self.comp_reqs,
            )
            # 持续计算的轻微正向奖励（由 operation 内部 shaping 为主）
            # step_reward += SUSTAINED_COMPUTE_BONUS

        # do_energy_dynamic(slot=self.slot_in_num, nodes=self.current_nodes, sm=self.SM)
        for _n in self.current_nodes:
            (_pi, _rho, _gamma, _static) = self.indicators[_n.id]
            if _gamma:
                _g = _n.charge(dt=self.slot_in_num)
                _n.gain_percent = _g * 100
                _gamma = False

            if _static:
                _s = _n.discharge_static(dt=self.slot_in_num)
                _n.cost_percent += _s * 100
                _static = False

            self.indicators[_n.id] = (_pi, _rho, _gamma, _static)



        (pi, rho, gamma, static) = self.indicators[node.id]
        if node.is_processing:
            if pi:
                _p = node.discharge_compute(dt=self.slot_in_num)
                node.cost_percent += _p * 100
                pi = False

        if node.is_communicating_isl:
            if rho:
                _r = node.discharge_isl(dt=self.slot_in_num)
                node.cost_percent += _r * 100
                rho = False

        self.indicators[node.id] = (pi, rho, gamma, static)


        # 轮询到下一个任务（下一步决策）
        self.current_task_idx += 1
        if self.current_task_idx >= len(self.current_tasks):
            # 本时间步所有任务均决策完毕，推进时间

            # do_energy_updating(slot=self.slot_in_num, nodes=self.current_nodes, sm=self.SM)

            delay_pen = compute_delay_penalty(self.slot_in_num, self.current_tasks)
            energy_pen = compute_energy_penalty(self.slot_in_num, self.current_nodes)

            aim_reward = reward_function(
                lamda=self.lamda,
                delay_penalty=delay_pen,
                energy_penalty=energy_pen,
                scale=10.0,
            )
            step_reward += aim_reward


            self.current_task_idx = 0
            self.discrete_time_update()

        if all_tasks_completed(self.task_manager.get_tasks()):
            step_reward += ALL_TASK_COMPLETION_REWARD
            terminated = True
            terminated_reason = "all_tasks_completed"
        elif any_satellite_depleted(self.current_nodes):
            step_reward += ENERGY_DROWN_PENALTY
            terminated = True
            terminated_reason = "satellite_energy_depleted"

        # _std = self.queue_variance()
        # step_reward += _std * -0.1
        # self.LG.info(f"Step {self.frame_counter}: Queue variance={_std:.4f} contributing reward={_std * -0.1:.4f}")


        obs, _ = get_obs(sm=self.state_manager, dm=self.decision_manager, step=self.frame_counter)

        # 使用 dict 替代 Info 对象，确保可序列化返回
        allowed = sorted(self.get_allowed_actions(task))
        valid_dirs = self.get_valid_dirs(task)

        info_serial = {
            "reward": float(step_reward),
            "truncated_reason": truncated_reason,
            "terminated_reason": terminated_reason,
            "is_truncated": bool(truncated),
            "is_terminated": bool(terminated),
            "allowed_actions": allowed,
            "valid_dirs": valid_dirs,
            "acted": int(act),
        }

        self.logger.info(f"Step {self.frame_counter} completed: reward={step_reward}, terminated={terminated} ({terminated_reason}), truncated={truncated} ({truncated_reason})")


        return obs, step_reward, terminated, truncated, info_serial

