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


class QueueScheduler:

    def update_queues_and_admission(self, tasks: List[Task]):
        T = self.PRED_WINDOW
        D = 1.0
        # 重建 QF：按任务当前所在节点分配到该节点的转发队列（待卸载决策）
        for s in self.sat:
            self.QF[s.id] = []
            # 清理已完成任务的 QB（仅保留未完成）
            self.QB[s.id] = [tid for tid in self.QB.get(s.id, []) if next((t for t in tasks if t.id == tid and not t.is_done), None)]
        for t in tasks:
            if t.is_done:
                continue
            node = next((sn for sn in self.sat if sn.plane == t.plane_at and sn.order == t.order_at), None)
            if node is None:
                continue
            self.QF.setdefault(node.id, []).append(t.id)
        # 准入：|QF_n| ≤ θ_n 且电量充足时，允许任务进入调度流程；超出则留待下一时隙
        for s in self.sat:
            qf_size = len(self.QF.get(s.id, []))
            theta = self.theta_n.get(s.id, 1)
            allow_energy = s.battery_ratio > 0.05
            # 若超过阈值，则将多余的任务延后（这里直接截断，保留前 θ_n 个作为本时隙可调度）
            if allow_energy and qf_size > theta:
                self.QF[s.id] = self.QF[s.id][:theta]

    def predict_future_loads(self):
        T = self.PRED_WINDOW
        alpha = self.ALPHA
        # 本地指数平滑预测 + 上限 η_n
        for s in self.sat:
            qb_cur = len(self.QB.get(s.id, []))
            qb_max = max(qb_cur, 1)
            eta_n = qb_max * math.sqrt(T) + 1.0
            series = self.pred_load.get(s.id, [qb_cur]*T)
            prev = series[0] if series else float(qb_cur)
            pred = alpha * prev + (1 - alpha) * float(qb_cur)
            seq = [max(1.0, min(pred, eta_n))]
            for _ in range(T-1):
                pred = alpha * pred + (1 - alpha) * float(qb_cur)
                seq.append(max(1.0, min(pred, eta_n)))
            self.pred_load[s.id] = seq
        # 与邻居共享：融合为 pred_load_shared
        gamma = 0.5
        for s in self.sat:
            isls = self.net.get_isl_of_node_at(s.id, self.period_counter, self.slot_counter)
            neigh_ids = [l.dst if l.src == s.id else l.src for l in isls] if isls else []
            local_seq = self.pred_load.get(s.id, [1.0]*T)
            if neigh_ids:
                neigh_seqs = [self.pred_load.get(nid, [1.0]*T) for nid in neigh_ids]
                avg_neigh = [float(np.mean([seq[k] for seq in neigh_seqs])) for k in range(T)]
                self.pred_load_shared[s.id] = [max(1.0, (1-gamma)*local_seq[k] + gamma*avg_neigh[k]) for k in range(T)]
            else:
                self.pred_load_shared[s.id] = [max(1.0, x) for x in local_seq]

    def get_hop_candidates(self, src: SatelliteEntity, max_hops: int = 1) -> List[SatelliteEntity]:
        visited = {src.id}
        frontier = {src.id}
        hops = 0
        result_ids: set[str] = set([src.id])
        while hops < max_hops and frontier:
            next_frontier = set()
            for nid in frontier:
                isls = self.net.get_isl_of_node_at(nid, self.period_counter, self.slot_counter)
                for l in isls:
                    neighbor = l.dst if l.src == nid else l.src
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)
                        result_ids.add(neighbor)
            frontier = next_frontier
            hops += 1
        return [s for s in self.sat if s.id in result_ids]

    def evaluate_task_on_candidates(self, task: Task, candidates: List[SatelliteEntity]) -> Dict[str, Tuple[float, float]]:
        # 待处理工作量 s'：按该层 GPU 秒数折算为步数
        n_layer = task.layer_id
        target_steps = max(1, math.ceil(LAYER_PROCESS_SECOND_COST_GPU[n_layer] / max(self.slot_in_num, 1e-6)))
        s_rem = float(target_steps)
        res: Dict[str, Tuple[float, float]] = {}
        # 源节点 n
        src = next((s for s in self.sat if s.plane == task.plane_at and s.order == task.order_at), None)
        src_id = src.id if src else None
        # 原始数据传输量（当前层输出）用于估算通信开销
        data_to_send = LAYER_OUTPUT_DATA_SIZE[n_layer]
        # 评估每个候选目的节点 m：采用目的节点的共享预测与算力，避免所有候选成本一致
        for m in candidates:
            t_prime = self.frame_counter
            e_acc = 0.0
            s_left = s_rem
            idx = 0
            m_cap = self.node_capacity.get(m.id, self.NODE_CAPACITY_PER_STEP)
            m_pred = self.pred_load_shared.get(m.id, [1.0]*self.PRED_WINDOW)
            # 若卸载到邻居，则加入简单通信时延估计（以最佳链路速率估算所需步数）
            if src_id and m.id != src_id:
                isls = self.net.get_isl_of_node_at(src_id, self.period_counter, self.slot_counter)
                link = None
                if isls:
                    link = next((l for l in isls if (l.src == src_id and l.dst == m.id) or (l.dst == src_id and l.src == m.id)), None)
                    if link is None:
                        # 不直接相邻则使用可用的最高速率近似一次转发
                        link = max(isls, key=lambda l: l.rate)
                if link and link.rate > 0:
                    comm_steps = math.ceil(data_to_send / (link.rate * self.slot_in_num))
                    t_prime += comm_steps
                    # 简单能耗模型：通信步数按 κ 缩放
                    e_acc += self.KAPPA * comm_steps
            # 目的节点上的计算共享（公平份额）
            while s_left > 0:
                load_m = max(m_pred[idx if idx < self.PRED_WINDOW else -1], 1.0)
                f_im = m_cap / load_m  # f_i,m(t') ← c_m / |QB*_m(t')|
                h_i = self.node_bottleneck.get(m.id, 1.0)
                r_im = min(f_im / h_i, s_left)
                e_acc += self.KAPPA * r_im * (f_im ** 2)
                s_left -= r_im
                t_prime += 1
                idx += 1
            d_cm = float(t_prime - self.frame_counter)
            res[m.id] = (d_cm, e_acc)
        return res

    def solve_ssp(self, tasks: List[Task], metrics: Dict[int, Dict[str, Tuple[float, float]]]) -> Tuple[Dict[int, str], Dict[int, str]]:
        w_delay, w_energy = 1.0, 1.0
        alpha: Dict[int, str] = {}
        beta: Dict[int, str] = {}
        for t in tasks:
            if t.is_done:
                continue
            src = next((s for s in self.sat if s.plane == t.plane_at and s.order == t.order_at), None)
            if src is None:
                continue
            isls = self.net.get_isl_of_node_at(src.id, self.period_counter, self.slot_counter)
            neighbors_id = set(l.dst if l.src == src.id else l.src for l in isls) if isls else set()
            allowed_ids = neighbors_id.union({src.id})
            best_node = src.id
            best_cost = float('inf')
            for nid, (d, e) in metrics.get(t.id, {}).items():
                if nid not in allowed_ids:
                    continue
                # Lyapunov 漂移-惩罚：在成本中加入队列项（以源节点 QF 长度近似漂移）
                drift_term = self.V * len(self.QF.get(src.id, []))
                cost = w_delay * d + w_energy * e + drift_term
                # 平局优先本地，避免固定选择同一邻居
                if cost < best_cost or (abs(cost - best_cost) < 1e-9 and nid == src.id):
                    best_cost = cost
                    best_node = nid
            if best_node == src.id:
                alpha[t.id] = src.id
            else:
                beta[t.id] = best_node
        return alpha, beta

