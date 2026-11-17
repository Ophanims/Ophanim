from collections import defaultdict
import logging
import os
import math
from typing import Dict, List, Tuple
import numpy as np
from simulator.schemas.project import Project
from datetime import datetime, timedelta, timezone
from simulator.services.network_service import LinkSnapshot, Network
from simulator.config import LAYER_OUTPUT_DATA_SIZE, LAYER_PROCESS_SECOND_COST_GPU, MAX_NUM_LAYERS
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


class OrbitScheduler:

    def get_alt_set(self) -> Dict[int, List[SatelliteEntity]]:
        """Algorithm 1: 为每个轨道计算候选集合 alt_set。
        依据当前周期计数与太阳照指示，输出每个轨道的可选卫星集合。
        返回值：按轨道分组的候选集合 dict[orbit_index] -> List[SatelliteEntity]
        """
        # 1. 获取轨道周期（用 self.orbital_period 表示周期步数）
        cyc = self.orbital_period

        # 2. 为每颗卫星计算其在 [t, t+cyc) 区间的日照时长与任务量估计
        # 将卫星按轨道分组
        orbits: Dict[int, List[SatelliteEntity]] = {}
        for s in self.sat:
            orbits.setdefault(s.plane, []).append(s)

        # 3. 估计每个轨道的 sunlit 与 task
        sunlit: Dict[int, float] = {}
        task_amount: Dict[int, float] = {}
        t = self.period_counter
        for orbit_idx, sats in orbits.items():
            # 累积该轨道上所有卫星在一个周期内的日照采样数
            sun_sum = 0.0
            for s in sats:
                sun_sum += s.sunlit_ratio(start=t, delta=cyc, step=1)
            # 归一化为 [0,1] 比例的总和（每颗卫星百分比求和）
            sunlit[orbit_idx] = sun_sum

            # 估计任务量：统计该轨道上的任务数量（或工作量）
            orbit_tasks = [k for k in self.task_manager.tasks if k.plane_at == orbit_idx and k.t_start <= t < k.t_end and not k.is_done]
            task_amount[orbit_idx] = float(len(orbit_tasks))

        # 4. 按 Algorithm 1 计算目标并分配 alt set
        # 计算权重与目标日照资源 target[i]
        total_task = sum(task_amount.values()) or 1.0
        total_sunlit = sum(sunlit.values())
        w: Dict[int, float] = {i: (task_amount[i] / total_task) for i in task_amount}
        target: Dict[int, float] = {i: (w[i] * total_sunlit - sunlit[i]) for i in sunlit}

        # 空闲轨道集合（任务量为 0）
        idle = {i for i, amt in task_amount.items() if amt == 0.0}

        # 背包选择：这里用简单贪心，以 sunlit 由大到小填充直到目标不为正
        alt_set_by_orbit: Dict[int, List[SatelliteEntity]] = {}
        for i, sats in orbits.items():
            # 该轨道自身永远加入
            subset: List[int] = []
            if target.get(i, 0.0) < 0:
                subset = []
            else:
                candidates = sorted(list(idle), key=lambda x: sunlit.get(x, 0.0), reverse=True)
                need = target.get(i, 0.0)
                picked = []
                acc = 0.0
                for j in candidates:
                    if acc >= need:
                        break
                    picked.append(j)
                    acc += sunlit.get(j, 0.0)
                subset = picked
                # 更新 idle 集
                for j in picked:
                    if j in idle:
                        idle.remove(j)

            # 构建该轨道的候选卫星集合：自身轨道 + 选择的空闲轨道的所有卫星
            chosen: List[SatelliteEntity] = []
            chosen.extend(sats)
            for j in subset:
                chosen.extend(orbits.get(j, []))
            alt_set_by_orbit[i] = chosen

        return alt_set_by_orbit

    def get_alt_ratio(self, sats: List[SatelliteEntity]) -> Dict[str, float]:
        """计算每颗卫星在一个轨道周期内的阳照比例（0~1）。"""
        alt_ratio: Dict[str, float] = {}
        for s in sats:
            alt_ratio[s.id] = float(s.sunlit_ratio(start=self.period_counter, delta=int(self.orbital_period), step=1))
        return alt_ratio

    def get_dod_ratio(self, sats: List[SatelliteEntity]) -> float:
        dod_ratio: Dict[str, float] = {}
        for s in sats:
            dod_ratio[s.id] = 1.0 - s.battery_ratio
        return dod_ratio

    def get_queue(self, tasks: List[Task]) -> Dict[str, int]:
        """返回每颗卫星上的排队任务数量。"""
        queue: defaultdict[str, int] = defaultdict(int)
        for t in tasks:
            _s = next((s for s in self.sat if s.plane == t.plane_at and s.order == t.order_at), None)
            if _s is None:
                continue
            queue[_s.id] += 1
        return dict(queue)

    def _arrange_processing(self, src: SatelliteEntity, t: int, tasks: List[Task]) -> Tuple[Dict[int, List[int]], int]:
        """Algorithm 3: 处理安排。
        返回 (X, flag_sun)，X 为任务到时间片的安排索引，flag_sun=1表示找到阳照时段优先安排。
        这里用简化：若当前节点处于阳照，则 flag_sun=1，并尽量在接下来连续步安排；否则在最晚可行窗口安排。
        """
        tasks_sorted = sorted(tasks, key=lambda k: k.ddl)
        X: Dict[int, List[int]] = {}
        flag_sun = 1 if src.is_charging else 0
        current = t

        total_proc_time = sum(LAYER_PROCESS_SECOND_COST_GPU[i] for i in range(len(LAYER_PROCESS_SECOND_COST_GPU)))
        T_cp = math.ceil(total_proc_time / self.period_in_num)

        for k in tasks_sorted:
            cp = T_cp  # 简化：单位计算时间
            # 若在阳照，尽量安排到当前时刻后连续 cp 步
            if flag_sun == 1:
                X[k.id] = list(range(current, current + cp))
            else:
                latest = max(t, k.ddl - cp)
                X[k.id] = list(range(latest, latest + cp))
            current = X[k.id][-1] + 1
        return X, flag_sun

    def _orbit_offloading(self, src: SatelliteEntity, k: Task, alt_set_by_orbit: Dict[int, List[SatelliteEntity]]) -> Tuple[str, Dict[int, List[int]]]:
        """Algorithm 2: 轨道内卸载决策。
        返回 (dst_id, X)，若下传地面满足时延则选择地面，否则依据候选集合选择邻居或本地处理。
        """
        # 地面站判定：检查链路与时延约束 Tgs + zk/Cap <= Tddl（近似）
        sgls: List[LinkSnapshot] = self.net.get_sgl_of_node_at(src.id, "SAT", self.period_counter, self.slot_counter)
        dst: str = ""
        X = {}
        if sgls:
            best = max(sgls, key=lambda l: l.rate)
            if best.rate > 0:
                # 估算数据量 zk（用当前层输出大小）与剩余截止时间 Tddl
                layer_idx = max(0, min(k.layer_id, len(LAYER_OUTPUT_DATA_SIZE) - 1))
                zk = float(LAYER_OUTPUT_DATA_SIZE[layer_idx])
                cap = float(best.rate)
                tddl = max(0, k.t_end - self.frame_counter)
                need = zk / cap if cap > 0 else math.inf
                if need <= tddl:
                    dst = best.dst

        # 本地安排
        Ks = [k]
        X_, flag_sun = self._arrange_processing(src, self.period_counter, Ks)
        hop_count = self.task_isl_hops.get(k.id, 0)
        self.logger.info(f"[OFFLOAD] node_id={src.id} battery={src.battery_ratio:.2f} charging={src.is_charging} flag_sun={flag_sun} dst={dst} isl_hops={hop_count}")

        if flag_sun == 1:
            dst = src.id
        else:
            # 若地面不可行，且尚未发生过ISL跳转，则择优单跳邻居；
            # 若已经发生过一次ISL跳转（单跳限制），则不再经由ISL，只允许本地或地面。
            if dst == "":
                if hop_count >= 1:
                    dst = src.id
                else:
                    # 只允许单跳：取实际ISL邻居和alt_set_by_orbit的交集
                    isls = self.net.get_isl_of_node_at(src.id, self.period_counter, self.slot_counter)
                    if isls:
                        neighbors_id = set(l.dst if l.src == src.id else l.src for l in isls)
                        candidates = alt_set_by_orbit.get(src.plane, [src])
                        single_hop_candidates = [s for s in candidates if s.id in neighbors_id]
                        if single_hop_candidates:
                            dst_n = max(single_hop_candidates, key=lambda s: getattr(s, "battery_ratio", 0.0))
                            dst = dst_n.id
                        else:
                            # 没有候选交集时，选择当前速率最高的直接邻居（仍为单跳）
                            link = max(isls, key=lambda l: l.rate)
                            backup = next(s for s in self.sat if s.id == (link.dst if link.src == src.id else link.src))
                            dst = backup.id
                    else:
                        dst = src.id

        if dst == src.id:
            X = X_

        self.logger.info(f"[OFFLOAD-RESULT] task_id={k.id} src_id={src.id} dst_id={dst} flag_sun={flag_sun} isl_hops={hop_count} X={X_}")
        return dst, X

