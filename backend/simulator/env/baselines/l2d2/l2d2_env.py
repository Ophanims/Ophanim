import logging
import os
import math
from typing import Dict, List, Tuple

import numpy as np
from simulator.schemas.project import Project
from datetime import datetime, timedelta, timezone

from simulator.services.network_service import LinkSnapshot, Network
from simulator.config import DEBUG, IMAGE_DATA_SIZE, LAYER_OUTPUT_DATA_SIZE, LOG_OUTPUT
from simulator.entities.earth_entity import EarthEntity
from simulator.entities.roi_entity import ROIEntity
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.entities.station_entity import StationEntity
from simulator.entities.sun_entity import SunEntity
from simulator.env.core.entity_col import EntityCol
from simulator.env.core.task_manager import TaskManager
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.env.vars.request import CompReq, TransReq


class L2D2Env:
    def __init__(self, input: Project):

        self.input = input

        self.t_start: datetime = datetime.now(timezone.utc)
        self.max_simulation_period: timedelta = timedelta(hours=2)  # 最大仿真时间
        self.t_end: datetime = self.t_start + self.max_simulation_period

        self.period_in_num: float = 30
        self.period: timedelta = timedelta(seconds=self.period_in_num)  # 时间步长，默认30秒
        self.max_period_numbers: int = math.ceil(self.max_simulation_period.total_seconds() / self.period_in_num)

        self.slot_in_num: float = 10
        self.slot: timedelta = timedelta(seconds=self.slot_in_num)  # 时间步长，默认5秒
        self.max_slot_number: int = math.ceil(self.period_in_num / self.slot_in_num)


        self.time_recorder: datetime = self.t_start

        self.period_counter: int = 0
        self.slot_counter: int = 0
        self.frame_counter: int = 0

        self.net: Network = None

        self.datetime_list: list[datetime] = []

        # Entities
        self.sat: List[SatelliteEntity] = []
        self.gs: List[StationEntity] = []
        self.roi: List[ROIEntity] = []
        self.eth: EarthEntity = None
        self.sun: SunEntity = None

        # Data storages
        self._gs_datas: List[dict] = []
        self._sat_datas: List[dict] = []

        # Entities Managers
        self.entity_collection = EntityCol(input)
        self.task_manager = TaskManager(self.entity_collection)

        self.at_ground = 0
        self.at_sunlit_sat = 0
        self.at_dark_sat = 0

    def setup(self, input: Project) -> None:
        """
        Reset and initialize simulation state using the provided project configuration.
        """
        metadata = load_input_metadata(input, self.max_simulation_period.total_seconds())

        self.t_start = metadata["t_start"]
        self.t_end = metadata["t_end"]
        if metadata["t_end"] > self.t_start:
            self.t_end = metadata["t_end"]

        self.time_recorder = metadata["time_recorder"]

        self.period = metadata["period"]
        self.max_period_numbers = metadata["max_period_numbers"]

        self.max_slot_number = math.ceil(self.period.total_seconds() / self.slot_in_num)

        self.datetime_list = metadata["datetime_list"]

        objs = build_static_objects(input, self.period, self.max_period_numbers, self.datetime_list)
        self.sat = objs['sat']
        self.gs = objs['gs']
        self.roi = objs['roi']
        self.eth = objs['eth']
        self.sun = objs['sun']
        self._sat_datas = objs['sat_datas']
        self._gs_datas = objs['gs_datas']
        self.net = init_network(input, self._sat_datas, self._gs_datas)
        self.period_update()

    def period_update(self):
        """
        Update all entities to the specified period time.
        """
        for s in self.sat:
            s.tick(self.period_counter, self.slot_counter)

        for g in self.gs:
            g.tick(self.period_counter, self.slot_counter)

        for r in self.roi:
            r.tick(self.period_counter, self.slot_counter)

        self.net._at(self.period_counter, self.slot_counter)

        if self.eth and self.sun:
            self.eth.tick(self.period_counter, self.slot_counter)
            self.sun.tick(self.period_counter, self.slot_counter)

    def reset(self):
        # 重新生成环境
        self.period_counter = self.slot_counter = self.frame_counter = 0
        self.setup(input=self.input)
        self.period_update()

        self.time_recorder = self.t_start
        self.period_counter = 0
        self.slot_counter = 0
        self.frame_counter = 0

        edges = self.net._all_links
        self.entity_collection.reset(self.sat, edges)

        all_nodes, all_edges, all_tasks = self.entity_collection.get_nodes(), self.entity_collection.get_edges(), self.task_manager.get_tasks()

        # self.SM.reset()
        # self.DM.reset()
        self.task_manager.reset()
        self.repeat_move_counts = {}

        # self.SM.setup(
        #     all_nodes=all_nodes,
        #     all_edges=all_edges,
        #     all_tasks=all_tasks
        # )

    # ---- 计算 Φ_t：为每个任务-地面站的价值矩阵 ----
    # 返回形状 (M, G)，M=当前任务数，G=地面站数量
    def compute_phi(self, tasks: List, gs_list: List[StationEntity]) -> np.ndarray:
        M = len(tasks)
        G = len(gs_list)
        if M == 0 or G == 0:
            return np.zeros((M, G), dtype=np.float32)

        phi = np.zeros((M, G), dtype=np.float32)
        # 简化的价值函数：可用链路的速率作为主要价值，结合SNR与距离做微调
        for i, task in enumerate(tasks):
            p, o = task.plane_at, task.order_at
            node = next((s for s in self.sat if s.plane == p and s.order == o), None)
            if node is None:
                continue
            sgl_links: List[LinkSnapshot] = self.net.get_sgl_of_node_at(node.id, "SAT", self.period_counter, self.slot_counter)
            for j, g in enumerate(gs_list):
                # 找到指向该地面站的链路（若存在）
                link = next((lk for lk in sgl_links if lk.dst == g.id), None)
                if link is None:
                    phi[i, j] = 0.0
                else:
                    # 价值：速率 * (1 + 0.1 * SNR) / (1 + 距离归一化)
                    dist_factor = 1.0 + (link.distance / 1e6)  # 距离的弱惩罚（以百万米归一）
                    phi[i, j] = float(link.rate) * (1.0 + 0.1 * float(link.snr)) / dist_factor
        return phi

    # ---- 计算带切换成本的贪心匹配 ----
    # 返回 permutation 数组 `perm`，长度为 M：任务 i 分配到地面站 perm[i]
    def greedy_assign_with_switch(self, phi_t: np.ndarray, prev_perm: List[int] | None, b: float) -> List[int]:
        M, G = phi_t.shape
        if M == 0 or G == 0:
            return []
        # B_t = b * P_{t-1}^T · Phi_t 等效为：若保持上一步同一地面站分配则给任务 i 的该地面站增加 b * phi_t[i, prev_perm[i]] 的收益
        adjustment = np.zeros_like(phi_t)
        if prev_perm is not None and len(prev_perm) == M:
            for i in range(M):
                j_prev = prev_perm[i]
                if 0 <= j_prev < G:
                    adjustment[i, j_prev] = b * phi_t[i, j_prev]
        score = phi_t + adjustment

        # 贪心选择：按最高得分排序，做一对一匹配（每个地面站最多服务一个任务；若要多任务共享，请移除此限制并在带宽分配处用公平比例）
        pairs: List[Tuple[int, int, float]] = []
        for i in range(M):
            j_best = int(np.argmax(score[i]))
            pairs.append((i, j_best, float(score[i, j_best])))
        # 按分数从高到低，避免冲突
        pairs.sort(key=lambda x: x[2], reverse=True)
        used_gs = set()
        perm = [-1] * M
        for i, j, _ in pairs:
            if j not in used_gs:
                perm[i] = j
                used_gs.add(j)
        # 未分配的任务，选其次优且未占用的地面站（若存在），否则保持 -1（此步不传）
        for i in range(M):
            if perm[i] == -1:
                order = np.argsort(score[i])[::-1]
                for j in order:
                    if j not in used_gs:
                        perm[i] = int(j)
                        used_gs.add(int(j))
                        break
        return perm

    def do_transferring(self, trans_reqs: List[Dict]):
        for req in trans_reqs:
            task_id = req["task_id"]

            node: SatelliteEntity = req["node"]
            node.is_communicating_sgl = True

            selected_link: LinkSnapshot = req["selected_link"]

            gs_id = selected_link.dst

            gs: StationEntity = next((g for g in self.gs if g.id == gs_id), None)
            gs.on_download = True

            task = next((t for t in self.task_manager.tasks if t.id == task_id), None)
            if task is None:
                continue

            # 得到当前需要传输的总数据量（原始层）
            target_data_to_send = IMAGE_DATA_SIZE

            # 获取当前通信速率
            comm_capacity = selected_link.rate
            if comm_capacity == 0:
                continue

            tasks_in_same_link = sum(1 for req in trans_reqs if req["dst"] == selected_link.dst)
            bandwidth_ratio = 1 / tasks_in_same_link if tasks_in_same_link > 0 else 0

            # 计算此步可传输的数据量
            data_this_step = comm_capacity * self.slot_in_num * bandwidth_ratio
            task.data_sent += data_this_step
            task.data_percent = task.data_sent / target_data_to_send

            if task.data_sent >= target_data_to_send:
                task.data_sent = 0.0
                task.data_percent = 0.0
                task.completion = 1.0
                task.is_done = True
                self.at_ground += 1

    def do_energy_updating(self, slot: float, nodes: List[SatelliteEntity]):
        for n in nodes:
            n.energy_step(dt=slot)

    # ---- L2D2 用的 step：返回下一步 Φ_t ----
    def step(self):
        # 初始化数值
        # self.SM.clear_progress_counters()
        # self.DM.reset()
        action_reward = 0.0
        trans_reqs = []
        # comp_reqs: List[CompReq] = [] 无处理任务

        terminated, truncated = False, False
        terminated_reason, truncated_reason = "None", "None"

        # 获取当前任务和节点状态
        # nodes, edges = self.EG.get_nodes(), self.EG.get_edges()
        nodes = self.sat
        edges = self.net.compute_isl_links_at(self.period_counter, self.slot_counter)

        all_tasks = self.task_manager.get_tasks()
        tasks = self.task_manager.get_tasks_at(step=self.frame_counter)
        n_tasks = len(tasks)

        # 初始化状态管理器和决策管理器的活跃任务数
        # self.SM.update(n_tasks)
        # self.DM.update(n_tasks)

        # 计算 Φ_t 矩阵并做带切换成本的匹配
        phi_t = self.compute_phi(tasks, self.gs)
        if not hasattr(self, "_prev_perm"):
            self._prev_perm = None
        perm = self.greedy_assign_with_switch(phi_t, self._prev_perm, b=0.1)
        self._prev_perm = perm[:] if len(perm) > 0 else None

        # 将匹配结果转换为传输请求
        for i, task in enumerate(tasks):
            if task.is_done:
                continue
            task.t_end += 1
            j = -1 if i >= len(perm) else perm[i]
            if j is None or j == -1 or j >= len(self.gs):
                continue
            p, o = task.plane_at, task.order_at
            node = next((s for s in self.sat if s.plane == p and s.order == o), None)
            if node is None:
                continue
            if node.battery_ratio <= 0:
                continue
            # 找链路：当前步面向该地面站的SGL
            sgl_links: List[LinkSnapshot] = self.net.get_sgl_of_node_at(node.id, "SAT", self.period_counter, self.slot_counter)
            link = next((lk for lk in sgl_links if lk.dst == self.gs[j].id), None)
            if link is None:
                continue
            trans_reqs.append({
                "task_id": task.id,
                "node": node,
                "dst": link.dst,
                "selected_link": link,
            })

        self.do_transferring(trans_reqs=trans_reqs)
        self.do_energy_updating(slot=self.slot_in_num, nodes=nodes)

        is_all_tasks_completed = all(t.is_done for t in all_tasks)
        if is_all_tasks_completed:
            terminated = True
            terminated_reason = "all_tasks_completed"

        # 使用 dict 替代 Info 对象，确保可序列化返回
        info_serial = {
            "num_nodes": len(nodes),
            "num_edges": len(edges),
            "num_tasks": n_tasks,
            "reward": 0.0,
            "truncated_reason": truncated_reason,
            "terminated_reason": terminated_reason,
            "is_truncated": truncated,
            "is_terminated": terminated,
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
                terminated = True
                terminated_reason = "max_period_reached"
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

        return 0.0, terminated, truncated, info_serial



