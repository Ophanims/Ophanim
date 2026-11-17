from simulator.env.baselines.mhspo.queue_scheduler import QueueScheduler
from collections import defaultdict
import logging
import os
import math
from typing import Dict, List, Tuple

import numpy as np
from simulator.schemas.project import Project
from datetime import datetime, timedelta, timezone

from simulator.services.network_service import LinkSnapshot, Network
from simulator.config import LAYER_OUTPUT_DATA_SIZE, LAYER_PROCESS_SECOND_COST_GPU, LOG_OUTPUT, MAX_NUM_LAYERS
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
from simulator.schemas.task import Task
from simulator.env.core.logger import SystemLogger


class MHSPOEnv(QueueScheduler):
    def __init__(self, input: Project):

        self.logger = SystemLogger("MHSPO")

        self.input = input

        self.t_start: datetime = datetime.now(timezone.utc)
        self.max_simulation_period: timedelta = timedelta(hours=2)  # 最大仿真时间
        self.t_end: datetime = self.t_start + self.max_simulation_period

        self.period_in_num: float = 30
        self.period: timedelta = timedelta(seconds=self.period_in_num)  # 时间步长，默认30秒
        self.max_period_numbers: int = math.ceil(self.max_simulation_period.total_seconds() / self.period_in_num)

        self.slot_in_num: float = 0.5
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

        # self.trans_reqs = []
        # self.comp_reqs = []
        # Track ISL hop counts per task to enforce single-hop
        self.task_isl_hops: Dict[int, int] = {}

        self.at_sunlit_sat = 0
        self.at_dark_sat = 0
        self.at_ground = 0

        # --- MHSPO 队列与参数 ---
        # QF: Forwarding/Offloading 队列（待卸载决策的任务）
        # QB: Computing 队列（已确定本地处理的任务）
        self.QF: Dict[str, List[int]] = {}
        self.QB: Dict[str, List[int]] = {}
        self.PRED_WINDOW: int = 10          # 预测窗口 T
        self.ALPHA: float = 0.9             # 指数平滑系数 α
        self.KAPPA: float = 1e-5            # 能耗系数 κ
        self.NODE_CAPACITY_PER_STEP: float = 1.0  # 归一化算力 c_n 默认 1.0
        self.pred_load: Dict[str, List[float]] = {}
        self.pred_load_shared: Dict[str, List[float]] = {}
        self.node_capacity: Dict[str, float] = {}
        self.node_bottleneck: Dict[str, float] = {}
        # Admission threshold per node θ_n（可依据算力/链路离线设定）
        self.theta_n: Dict[str, int] = {}
        # Lyapunov 权衡参数 V 与最大可允许多跳
        self.V: float = 1.0
        self.MAX_HOPS: int = 2

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

        orbital_period = input.constellation.orbital_period
        self.orbital_period = math.ceil(orbital_period / self.period_in_num)

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

        self.task_manager.reset(slot=self.slot_in_num)
        self.repeat_move_counts = {}

        self.trans_reqs = []
        self.comp_reqs = []
        self.task_isl_hops = {}
        # 初始化 MHSPO 队列与预测结构
        self.QF = {s.id: [] for s in self.sat}
        self.QB = {s.id: [] for s in self.sat}
        self.pred_load = {s.id: [1.0]*self.PRED_WINDOW for s in self.sat}
        self.pred_load_shared = {s.id: [1.0]*self.PRED_WINDOW for s in self.sat}
        # 初始化每节点算力 c_n 与瓶颈 h_i（可按设备差异化配置）
        self.node_capacity = {s.id: self.NODE_CAPACITY_PER_STEP for s in self.sat}
        self.node_bottleneck = {s.id: 1.0 for s in self.sat}
        # θ_n 默认按算力近似（可按离线配置覆盖）
        self.theta_n = {s.id: int(max(1, math.ceil(self.node_capacity[s.id] * 5)) ) for s in self.sat}


    def do_transferring(self):
        for req in list(self.trans_reqs):
            task_id = req["task_id"]

            task = next((t for t in self.task_manager.tasks if t.id == task_id), None)
            if task is None:
                continue

            node: SatelliteEntity = req["node"]

            selected_link: LinkSnapshot = req["selected_link"]

            if req["type"] == "isl":

                node.is_communicating_isl = True

                tar_sat: SatelliteEntity = next((s for s in self.sat if s.id == req["dst"]), None)

                tar_p = tar_sat.plane
                tar_o = tar_sat.order
                n_p = node.plane
                n_o = node.order

                dp = tar_p - n_p
                do = tar_o - n_o

                if dp == 1 and do == 0:
                    direction = 1
                elif dp == -1 and do == 0:
                    direction = 2
                elif dp == 0 and do == 1:
                    direction = 3
                else:
                    direction = 4
                task.acted = direction

            else:
                node.is_communicating_sgl = True

                gs_id = selected_link.dst

                gs: StationEntity = next((g for g in self.gs if g.id == gs_id), None)
                gs.on_download = True

            # 得到当前需要传输的总数据量（原始层）
            # target_data_to_send = IMAGE_DATA_SIZE
            n = task.layer_id
            target_data_to_send = LAYER_OUTPUT_DATA_SIZE[n]

            # 获取当前通信速率
            comm_capacity = selected_link.rate
            if comm_capacity == 0:
                continue

            tasks_in_same_link = sum(1 for req in self.trans_reqs if req["dst"] == selected_link.dst)
            # 如果只有当前任务占用该链路，带宽比例应为1；否则按平均分配
            bandwidth_ratio = 1 / tasks_in_same_link if tasks_in_same_link > 0 else 1

            # 计算此步可传输的数据量
            data_this_step = comm_capacity * self.slot_in_num * bandwidth_ratio
            task.data_sent += data_this_step
            task.data_percent = task.data_sent / target_data_to_send

            if task.data_sent >= target_data_to_send:
                self.trans_reqs.remove(req)
                task.data_sent = 0.0
                task.data_percent = 0.0
                if req["type"] == "isl":
                    # 卸载到目标卫星，更新任务位置
                    task.plane_at = tar_sat.plane
                    task.order_at = tar_sat.order
                    self.task_isl_hops[task.id] = self.task_isl_hops.get(task.id, 0) + 1
                    # 记录已发生一次ISL跳转，并释放通信占用标志
                    node.is_communicating_isl = False
                else:
                    task.completion = 1.0
                    task.is_done = True
                    # 释放SGL占用标志
                    node.is_communicating_sgl = False
                    self.at_ground += 1
                    if 'gs' in locals() and isinstance(gs, StationEntity):
                        gs.on_download = False

    def do_energy_updating(self, slot: float, nodes: List[SatelliteEntity]):
        for n in nodes:
            n.energy_step(dt=slot)

    def do_computing(
        self,
        slot: float,
        tasks: List[Task],
    ):
        # LAYER_PROCESS_STEP_COST = [math.ceil(i * STEP_PER_SECOND) for i in LAYER_PROCESS_SECOND_COST_GPU]
        # 处理每个传输请求
        for req in list(self.comp_reqs):

            m = req["task_id"]

            # 找到对应的任务对象
            task = next((task for task in tasks if task.id == m), None)
            if task is None:
                continue

            node: SatelliteEntity = req["node"]
            node.is_processing = True

            if node.is_charging:
                self.at_sunlit_sat += 1
            else:
                self.at_dark_sat += 1

            # 得到当前需要计算的总工作量
            n = task.layer_id
            target = LAYER_PROCESS_SECOND_COST_GPU[n] / slot

            # 更新计算进度 (记录前进度以计算增量奖励)
            task.workload_done += 1
            task.workload_percent = task.workload_done / target
            # 奖励塑形：每步计算给予微奖励，降低纯稀疏奖励带来的探索困难

            # 检查是否完成计算
            if task.workload_done >= target:
                self.comp_reqs.remove(req)
                # 计算完成：进入下一层
                task.layer_id += 1
                task.workload_done = 0
                task.workload_percent = 0.0

                # 正确的完成度应基于更新后的 task.layer_id
                task.completion = task.layer_id / MAX_NUM_LAYERS

                # 检查任务是否完成
                if task.layer_id >= MAX_NUM_LAYERS:
                    task.is_done = True

    # ---------------- Algorithm 2: 队列更新与准入 ----------------

    # ---------------- Algorithm 1: 负载预测与邻居共享 ----------------

    # ---------------- 候选集（单跳 / 最多双跳） ----------------

    # ---------------- Algorithm 1 中的时延/能耗评估 ----------------

    # ---------------- SSP 启发式调度（本地/邻居二选一） ----------------

    def step(self):
        # 初始化数值

        terminated, truncated = False, False
        terminated_reason, truncated_reason = "None", "None"

        # 获取当前任务和节点状态
        nodes = self.sat
        edges = self.net.compute_isl_links_at(self.period_counter, self.slot_counter)

        all_tasks = self.task_manager.get_tasks()
        tasks = self.task_manager.get_tasks_at(step=self.frame_counter)
        n_tasks = len(tasks)

        # 依据 Algorithm 1 生成按轨道的候选集合
        # 队列更新 + 准入（Algorithm 2 步骤1-4）
        self.update_queues_and_admission(tasks)
        # 负载预测（Algorithm 1 步骤1-6）
        # 动态设置预测窗口为未完成任务最大DDL
        all_ddl = [t.ddl for t in all_tasks if not t.is_done]
        self.PRED_WINDOW = max(all_ddl) if all_ddl else self.PRED_WINDOW
        self.predict_future_loads()

        # 构建候选集（单跳）并评估（Algorithm 1 步骤7-16）
        metrics: Dict[int, Dict[str, Tuple[float, float]]] = {}
        for task in tasks:
            if task.is_done:
                continue
            task.t_end += 1
            # 去重：正在计算或传输中的任务不可再调度
            if any(r["task_id"] == task.id for r in self.comp_reqs) or any(r["task_id"] == task.id for r in self.trans_reqs):
                continue
            node = next((s for s in self.sat if s.plane == task.plane_at and s.order == task.order_at), None)
            if node is None or node.battery_ratio <= 0:
                continue
            # 仅评估已准入任务（在 QF 内）
            if task.id not in self.QF.get(node.id, []):
                continue
            candidates = self.get_hop_candidates(node, max_hops=self.MAX_HOPS)
            evals = self.evaluate_task_on_candidates(task, candidates)
            metrics[task.id] = evals

        # SSP 调度得到 α/β（Algorithm 2 步骤10）
        alpha, beta = self.solve_ssp(tasks, metrics)

        # 将匹配结果转换为传输/计算请求（Algorithm 2 驱动）
        for task in tasks:

            # 去重：若已完成则跳过
            if task.is_done:
                continue

            # 更新时间窗口
            task.t_end += 1

            # 去重：若已在队列中则跳过
            if any(r["task_id"] == task.id for r in self.comp_reqs) or any(r["task_id"] == task.id for r in self.trans_reqs):
                continue

            # 找到任务所在节点，没电或节点不存在则跳过
            node = next((s for s in self.sat if s.plane == task.plane_at and s.order == task.order_at), None)
            if node is None or node.battery_ratio <= 0:
                continue

            # 依据 SSP 结果选择目的地（本地或邻居）
            dst_id = alpha.get(task.id, beta.get(task.id, node.id))
            if dst_id == node.id:
                # 本地处理请求
                is_sat_computing_occupied = any(r["node"].id == node.id for r in self.comp_reqs)
                if node.is_processing is False and not is_sat_computing_occupied:
                    self.comp_reqs.append({
                        "task_id": task.id,
                        "node": node,
                    })
                    # 进入本地计算队列 QB
                    if task.id not in self.QB.get(node.id, []):
                        self.QB.setdefault(node.id, []).append(task.id)
            else:
                # 地面或其它卫星传输
                if dst_id.startswith("GS"):
                    print("Request SGL transfer")
                    sgls = self.net.get_sgl_of_node_at(node.id, "SAT", self.period_counter, self.slot_counter)
                    if not sgls:
                        continue
                    link = max(sgls, key=lambda l: l.rate)
                    self.trans_reqs.append({
                        "type": "sgl",
                        "task_id": task.id,
                        "node": node,
                        "dst": link.dst,
                        "selected_link": link,
                    })
                else:
                    isls = self.net.get_isl_of_node_at(node.id, self.period_counter, self.slot_counter)
                    if not isls:
                        continue
                    link = next((l for l in isls if (l.src == node.id and l.dst == dst_id) or (l.dst == node.id and l.src == dst_id)), None)
                    if link is None:
                        # link = max(isls, key=lambda l: l.rate)
                        continue

                    self.trans_reqs.append({
                        "type": "isl",
                        "task_id": task.id,
                        "node": node,
                        "dst": dst_id,
                        "selected_link": link,
                    })

        self.do_transferring()
        self.do_computing(
            slot=self.slot_in_num,
            tasks=tasks,
        )
        self.do_energy_updating(
            slot=self.slot_in_num,
            nodes=nodes
        )

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

        print(f"Slot {self.frame_counter}")
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
