"""Per-task action selection against one detached state; no physics or clock."""
from simulator.policies.base import SchedulingPolicy
from simulator.policies.discrete_actions import DiscreteActions
from simulator.core.actions import ComputeAction, SchedulingActions, TransferAction
from simulator.config import IDLE_PENALTY, LAYER_OUTPUT_DATA_SIZE
from simulator.env.vars.request import CompReq, TransReq
from simulator.env.io.state_manager import StateManager
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.core.observation import get_obs


class DiscreteScheduler(DiscreteActions, SchedulingPolicy):
    def begin(self, view):
        self._view = view
        self.current_tasks = view.task_manager.get_tasks_at(view.frame_counter)
        self.current_nodes = view.sat
        self.current_edges = view.net.compute_isl_links_at(view.period_counter, view.slot_counter)
        self.current_task_idx = 0
        tasks = {task.id: task for task in view.task_manager.tasks}
        nodes = {node.id: node for node in view.sat}
        self.comp_reqs = [CompReq(tasks[r["task_id"]], r["node"]) for r in view.comp_reqs]
        self.trans_reqs = [TransReq(tasks[r["task_id"]], r["node"], nodes[r["dst"]]) for r in view.trans_reqs]
        self.state_manager = StateManager(view.entity_collection.number_of_planes,
                                          view.entity_collection.number_of_sat_per_planes)
        self.decision_manager = DecisionManager(self.state_manager.P_MAX, self.state_manager.O_MAX)
        self.state_manager.setup(self.current_nodes, self.current_edges)
        self.state_manager.update(self.current_tasks, self.current_nodes, self.current_edges)

    @property
    def finished(self):
        return self.current_task_idx >= len(self.current_tasks)

    def observation(self):
        return get_obs(self.state_manager, self.decision_manager, self.frame_counter)[0]

    def submit(self, action):
        if self.finished:
            return 0.0
        reward = self.select_action(action)
        self.current_task_idx += 1
        return reward

    def actions(self):
        return SchedulingActions(
            compute=tuple(ComputeAction(r.task.id, r.node.id) for r in self.comp_reqs),
            transfer=tuple(TransferAction(r.task.id, r.src.id, r.dst.id, "isl",
                weight=LAYER_OUTPUT_DATA_SIZE[r.task.layer_id]) for r in self.trans_reqs))

    def select_action(self, action):
        act = int(action)
        step_reward = 0.0
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

        if not com_req and not tr_req and not is_no_energy:
            # 强化奖励设计
            if act == 0:
                step_reward += IDLE_PENALTY

            elif act in [1, 2, 3, 4]:
                # prev_act = task.acted

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
            elif act == 5:
                is_occupied = any(c.node.id == node.id for c in self.comp_reqs)
                if not is_occupied:
                    # 只有从“动/空转”切到可用的计算节点时，给一次小 bonus

                    com_req = CompReq(task=task, node=node)
                    self.comp_reqs.append(com_req)
            task.acted = act

        return step_reward
