import numpy as np
from typing import Dict, List, Tuple
import logging

from simulator.config import DEBUG, MAX_NUM_LAYERS, MAX_NUM_TASKS
from simulator.schemas.task import Task
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.services.network_service import LinkSnapshot


class StateManager:
    def __init__(self, p_max: int, o_max: int):
        # active task count
        self.task_id_list: List[int] = []
        # history buffer for snapshots
        self._beta: Dict[int, Dict[str, np.ndarray]] = {}

        # size limits
        self.P_MAX = p_max
        self.O_MAX = o_max

        # Internal storages (sparse dicts). Keys are tuples; values are scalars.
        # Topology
        self.energy: Dict[Tuple[int, int], float] = {}
        self.sunlight: Dict[Tuple[int, int], int] = {}
        # Directed link capacities: (up,uo,vp,vo) -> float rate
        self.comm: Dict[Tuple[int, int, int, int], float] = {}
        # Per-node task load/queue percent: (p,o) -> float
        self.queue: Dict[Tuple[int, int], float] = {}

        # Tasks
        # m -> (p,o)
        self.location: Dict[int, Tuple[int, int]] = {}
        # m -> current layer index
        self.completion: Dict[int, float] = {}
        # per-task timing for latency feature
        # m -> int (task start slot)
        self.t_start_map: Dict[int, int] = {}
        # m -> int (task current end slot)
        self.t_end_map: Dict[int, int] = {}
        # m -> int (task deadline slot)
        self.ddl_map: Dict[int, int] = {}
        # m -> float/int (per-task size metric, e.g., data_percent)
        self.size: Dict[int, float] = {}
        # m -> float/int (per-task workload metric, e.g., workload_percent)
        self.workload: Dict[int, float] = {}


    def setup(self, all_nodes: List[SatelliteEntity], all_edges: List[LinkSnapshot]):
        for n in all_nodes:
            pp, oo = int(n.plane), int(n.order)
            self.energy[(pp, oo)] = float(n.battery_ratio)
            self.sunlight[(pp, oo)] = int(n.is_charging)
            self.queue[(pp, oo)] = float(n.task_queue_percent)

        for e in all_edges:
            # defensive: map ids -> nodes (may be None if link is to GS etc)
            u = next((n for n in all_nodes if n.id == e.src), None)
            v = next((n for n in all_nodes if n.id == e.dst), None)
            if u is None or v is None:
                if DEBUG:
                    print("StateManager.setup: skipping edge for unknown node src=%s dst=%s", e.src, e.dst)
                continue

            src_p, src_o = int(u.plane), int(u.order)
            dst_p, dst_o = int(v.plane), int(v.order)

            # avoid duplicate initialization — if already set and similar rate, skip or keep max
            existing = float(self.comm.get((src_p, src_o, dst_p, dst_o), 0.0))
            new_rate = float(e.rate)
            if existing != 0.0:
                # keep the maximum rate to be safe and avoid duplicate prints
                if new_rate > existing:
                    self.comm[(src_p, src_o, dst_p, dst_o)] = new_rate
                    self.comm[(dst_p, dst_o, src_p, src_o)] = new_rate
                    if DEBUG:
                        print("StateManager.setup: updated comm link U(%d,%d)<->V(%d,%d) to higher rate %f", src_p, src_o, dst_p, dst_o, new_rate)
                else:
                    if DEBUG:
                        print("StateManager.setup: skipping duplicate comm link U(%d,%d)<->V(%d,%d) (existing=%f new=%f)", src_p, src_o, dst_p, dst_o, existing, new_rate)
                continue

            self.comm[(src_p, src_o, dst_p, dst_o)] = new_rate
            self.comm[(dst_p, dst_o, src_p, src_o)] = new_rate
            if DEBUG:
                print("StateManager.setup: initialized comm link U(%d,%d) <-> V(%d,%d) with rate %f", src_p, src_o, dst_p, dst_o, new_rate)


    def update(self, tasks: List[Task], all_nodes: List[SatelliteEntity], all_edges: List[LinkSnapshot]):
        """
        用当前时刻的任务覆盖性更新任务视图：
        - 不再追加（append），而是重建 task_id_list，保持与当前 tasks 一一对应；
        - 位置与进度字典按任务 id 更新。
        """
        self.task_id_list = [int(t.id) for t in tasks]
        for t in tasks:
            self.location[int(t.id)] = (int(t.plane_at), int(t.order_at))
            self.completion[int(t.id)] = float(t.completion)
            # record timing for latency computation
            self.t_start_map[int(t.id)] = int(getattr(t, "t_start", 0))
            self.t_end_map[int(t.id)] = int(getattr(t, "t_end", 0))
            self.ddl_map[int(t.id)] = int(getattr(t, "ddl", 0))

        for n in all_nodes:
            pp, oo = int(n.plane), int(n.order)
            self.energy[(pp, oo)] = float(n.battery_ratio)
            self.sunlight[(pp, oo)] = int(n.is_charging)
            self.queue[(pp, oo)] = float(n.task_queue_percent)

        for e in all_edges:
            # defensive: map ids -> nodes (may be None if link is to GS etc)
            u = next((n for n in all_nodes if n.id == e.src), None)
            v = next((n for n in all_nodes if n.id == e.dst), None)
            if u is None or v is None:
                continue

            src_p, src_o = int(u.plane), int(u.order)
            dst_p, dst_o = int(v.plane), int(v.order)

            _rate = float(e.rate)

            self.comm[(src_p, src_o, dst_p, dst_o)] = _rate
            self.comm[(dst_p, dst_o, src_p, src_o)] = _rate

    def report(self, step: int) -> Dict[str, np.ndarray]:
        beta_t = self._to_beta()
        self._beta[step] = beta_t
        return beta_t

    def reset(self):
        self.task_id_list = []
        self.energy.clear()
        self.sunlight.clear()
        self.comm.clear()
        self.location.clear()
        self.completion.clear()
        self.t_start_map.clear()
        self.t_end_map.clear()
        self.ddl_map.clear()
        self.size.clear()
        self.workload.clear()

    def write_energy(self, p: int, o: int, value: float):
        self.energy[(int(p), int(o))] = float(value)

    def write_sunlight(self, p: int, o: int, value: int):
        self.sunlight[(int(p), int(o))] = int(value)

    def write_comm(self, u: Tuple[int, int], v: Tuple[int, int], value: float):
        up, uo = int(u[0]), int(u[1])
        vp, vo = int(v[0]), int(v[1])
        self.comm[(up, uo, vp, vo)] = float(value)

    def write_location(self, m: int, value: Tuple[int, int]):
        self.location[int(m)] = (int(value[0]), int(value[1]))

    def write_progress(self, m: int, value: int):
        self.completion[int(m)] = int(value)

    def write_size(self, m: int, value: float):
        # record per-task size metric (e.g., cumulative percent)
        self.size[int(m)] = float(value)

    def write_workload(self, m: int, value: float):
        # record per-task workload metric (e.g., cumulative percent)
        self.workload[int(m)] = float(value)

    def clear_progress_counters(self):
        """Clear per-step increment counters (call at the start of each env.step)."""
        # workload and size may represent per-step increments
        # Clear per-step increments
        self.workload.clear()
        self.size.clear()

    def get_comm(self, u: Tuple[int, int], v: Tuple[int, int]) -> float:
        up, uo = int(u[0]), int(u[1])
        vp, vo = int(v[0]), int(v[1])
        return float(self.comm.get((up, uo, vp, vo), 0.0))

    def get_size(self, m: int, n: int) -> float:
        return float(self.size.get((int(m), int(n)), 0.0))

    def get_progress(self, m: int) -> int:
        return int(self.completion.get(int(m), 0))

    def get_location(self, m: int) -> Tuple[int, int]:
        return tuple(self.location.get(int(m), (0, 0)))

    def neighbors_of(self, u: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Return list of neighbors v for which a link exists from or to u.
        Uses current directed comm entries.
        """
        up, uo = int(u[0]), int(u[1])
        nbrs: List[Tuple[int, int]] = []
        for (sp, so, tp, to), rate in ((k, v) for k, v in self.comm.items() if v and v != 0):
            if sp == up and so == uo:
                nbrs.append((tp, to))
            elif tp == up and to == uo:
                nbrs.append((sp, so))
        # unique
        seen = set()
        uniq = []
        for v in nbrs:
            if v not in seen:
                uniq.append(v)
                seen.add(v)
        return uniq

    def _to_beta(self) -> Dict[str, np.ndarray]:
        """Return a snapshot of current state (beta) with topology full-shape
        and task arrays limited to the first self._M active tasks.
        """
        # Build dense arrays for observation compatibility
        energy_arr = np.zeros((self.P_MAX, self.O_MAX), dtype=np.float32)
        for (p, o), val in self.energy.items():
            if 0 <= p < self.P_MAX and 0 <= o < self.O_MAX:
                energy_arr[p, o] = float(val)

        sunlight_arr = np.zeros((self.P_MAX, self.O_MAX), dtype=np.float32)
        for (p, o), val in self.sunlight.items():
            if 0 <= p < self.P_MAX and 0 <= o < self.O_MAX:
                sunlight_arr[p, o] = float(val)

        comm_arr = np.zeros((self.P_MAX, self.O_MAX, self.P_MAX, self.O_MAX), dtype=np.float32)
        for (up, uo, vp, vo), val in self.comm.items():
            if 0 <= up < self.P_MAX and 0 <= uo < self.O_MAX and 0 <= vp < self.P_MAX and 0 <= vo < self.O_MAX:
                comm_arr[up, uo, vp, vo] = float(val)

        # queue/load per node
        queue_arr = np.zeros((self.P_MAX, self.O_MAX), dtype=np.float32)
        for (p, o), val in self.queue.items():
            if 0 <= p < self.P_MAX and 0 <= o < self.O_MAX:
                queue_arr[p, o] = float(val)

        M = len(self.task_id_list)
        location_arr = np.zeros((M, 2), dtype=np.int32)
        progress_arr = np.zeros((M,), dtype=np.int32)
        size_arr = np.zeros((M,), dtype=np.float32)
        workload_arr = np.zeros((M,), dtype=np.float32)

        # 注意：这里按当前顺序“压缩”到 0..M-1 索引，避免用任务 id 直接索引越界
        for idx, m_id in enumerate(self.task_id_list):
            if m_id in self.location:
                p, o = self.location[m_id]
                location_arr[idx, 0] = int(p)
                location_arr[idx, 1] = int(o)
            if m_id in self.completion:
                progress_arr[idx] = int(self.completion[m_id])
            # sizes/workload: per-task metric only
            size_arr[idx] = float(self.size.get(m_id, 0.0))
            workload_arr[idx] = float(self.workload.get(m_id, 0.0))

        beta_t = {
            "energy": energy_arr,
            "sunlight": sunlight_arr,
            "comm": comm_arr,
            "location": location_arr,
            "progress": progress_arr,
            "size": size_arr,
            "workload": workload_arr,
            "queue": queue_arr,
        }

        return beta_t

    def sum_size_before(self, m: int, n: int, T: int) -> float:
        """
        获取t时间之前所有size[m, n]历史值，返回float字典。
        """
        result = 0.0
        # Sum historical snapshots strictly before T (per-task vectors)
        for t in range(T):
            beta = self._beta.get(t)
            if beta is None:
                continue
            arr = beta.get("size")
            if arr is None:
                continue
            if getattr(arr, 'ndim', 0) == 1 and 0 <= m < arr.shape[0]:
                result += float(arr[m])
        # include current in-memory buffer for step T (ignore n)
        result += float(self.size.get(int(m), 0.0))
        return result

    def sum_workload_before(self, m: int, n: int, T: int) -> int:
        """
        获取t时间之前所有workload[m, n]历史值，返回int字典。
        """
        result = 0.0
        # Sum historical snapshots strictly before T (per-task vectors)
        for t in range(T):
            beta = self._beta.get(t)
            if beta is None:
                continue
            arr = beta.get("workload")
            if arr is None:
                continue
            if getattr(arr, 'ndim', 0) == 1 and 0 <= m < arr.shape[0]:
                result += float(arr[m])
        # include current in-memory buffer for step T (ignore n)
        result += float(self.workload.get(int(m), 0.0))
        return int(result)

    def is_empty(self) -> bool:
        """
        检查状态管理器是否为空（没有初始化数据）。
        :return: 是否为空 (bool)
        """
        return len(self.task_id_list) == 0
