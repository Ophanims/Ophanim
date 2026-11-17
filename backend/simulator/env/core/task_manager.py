# TaskManager: 任务生成与管理
import numpy as np
from typing import List

from simulator.config import LAYER_PROCESS_SECOND_COST_GPU, MAX_NUM_TASKS
from simulator.env.core.entity_col import EntityCol
from simulator.schemas.task import Task


class TaskManager:
    def __init__(self, eg: EntityCol):
        self.eg = eg
        self.seed = eg.seed
        self.rng = np.random.default_rng(self.seed)
        self.tasks: List[Task] = []

    def generate(self, slot: float = 1.0):
        node_keys = list(self.eg.nodes_dict.keys())
        # 如果没有任何节点，跳过任务生成以避免 self.rng.integers(0, 0))

        total_proc_time = sum(LAYER_PROCESS_SECOND_COST_GPU[i] for i in range(len(LAYER_PROCESS_SECOND_COST_GPU)))
        total_proc_steps = total_proc_time / slot

        if len(node_keys) == 0:
            self.tasks = []
            return

        # 统计每个节点分配任务次数
        node_task_count = {k: 0 for k in node_keys}
        _id = 0
        while _id < MAX_NUM_TASKS:
            idx = self.rng.integers(0, len(node_keys))
            (_plane_at, _order_at) = node_keys[idx]
            # if node_task_count[(_plane_at, _order_at)] >= 5:
            #     continue  # 跳过已分配超过5次的节点
            _t = self.rng.integers(0, 40)
            task_obj = Task(
                id=_id,
                layer_id=0,
                plane_at=_plane_at,
                order_at=_order_at,
                t_start=_t,
                t_end=_t,
                acted=0,
                workload_done=0,
                data_sent=0,
                is_done=False,
                ddl = _t + 3 * total_proc_steps,
            )
            self.tasks.append(task_obj)
            node_task_count[(_plane_at, _order_at)] += 1
            _id += 1

    def reset(self, slot: float = 1.0, seed: int | None = None):
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.tasks.clear()
        self.generate(slot=slot)

    def get_tasks_at(self, step: int) -> List[Task]:
        return [t for t in self.tasks if not t.t_start > step and not t.is_done]

    def get_all_finished_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.is_done]

    def get_tasks(self) -> List[Task]:
        return self.tasks

    def task_state(self, task: Task):

        # --- Case 1: 已完成 ---
        if task.is_done:
            return "done"

        # --- Case 2: computing ---
        # 条件：上一动作是 compute 且已计算过部分
        if task.acted == 5 and task.workload_done > 0:
            return "under_processing"

        # --- Case 3: transferring ---
        # 条件：上一动作是传输且方向一致
        if task.acted in [1, 2, 3, 4] and task.data_sent > 0:
            return "under_transferring"

        # --- Case 4: idle ---
        return "idle"
