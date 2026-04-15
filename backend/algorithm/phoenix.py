import math
from typing import Dict, List, Set, Tuple

from algorithm.algo import Algorithm
from status.mission_status import MissionStatus
from entity.world import WORLD
from entity.mission import Mission
from entity.gs import GroundStation
from entity.sat import Satellite
from topology.node import Node
from topology.link import Link
from skyfield.timelib import Time

class PhoenixAlgorithm(Algorithm):
    """默认算法：不改变行为，仅保留三阶段流程结构。"""

    def observe(self) -> dict:
        world = WORLD
        nodes = world.nodes
        links = world.links
        topology = (nodes, links)
        current_time = world.current_time
        current_slot = world.current_slot
        
    def decide(self, satellite: "Satellite", state: dict) -> dict:
        return {}

    def act(self, satellite: "Satellite", action: dict) -> None:
        pass
    
    # 原论文中并没有给出 Knapsack 和 检索最早阳光 的具体实现，
    # 这里提供一个简单的版本作为示范。
    def _find_next_sunlit_slot(self, s: Satellite, t: Time, t_slot: int) -> int:
        """辅助函数：搜索从 start_slot 开始的第一个日照时刻"""
        # 搜索上限可设为当前轨道周期，防止死循环
        cyc_slot = t_slot + s.get_orbital_cycle() // WORLD.SLOT
        for tau in range(t_slot, cyc_slot + 1):
            _t: Time = t + tau * WORLD.SLOT
            if s.is_sunlit(_t):
                return tau
        return t_slot # 若无阳光，返回当前最早可用时间
    
    def _knapsack(self, 
        idle_orbits: list[int], 
        sunlit_values: dict[int, float], 
        target_value: float):
        """
        一个简单的 0/1 背包算法变体。
        目标：从 idle_orbits 中选择一组轨道，使其 sunlit 总和尽量接近并覆盖 target_value。
        """
        if target_value <= 0 or not idle_orbits:
            return []

        # 提取备选轨道的阳光值
        items = [(orbit_id, sunlit_values[orbit_id]) for orbit_id in idle_orbits]
        n = len(items)
        
        # 使用动态规划求解
        # dp[i] 表示达到阳光值 i 是否可行
        # 这里我们简化处理，由于是分配资源，采用贪心或标准背包均可
        # 下面采用贪心策略（优先选阳光值大的）作为示范，也可替换为精确 DP
        items.sort(key=lambda x: x[1], reverse=True)
        
        selected_subset = []
        current_sum = 0
        for orbit_id, val in items:
            if current_sum < target_value:
                selected_subset.append(orbit_id)
                current_sum += val
            else:
                break
                
        return selected_subset
    
    # Algorithm 1
    def _sunlight_aware_orbit_assignment(self, 
        topology: Tuple[List[Node], List[Link]], 
        tasks: List[Mission], 
        t: Time, 
        t_slot: int):
        """基于卫星与太阳的相对位置，动态调整卫星轨道以最大化太阳能利用率。"""
        # Input: 卫星当前轨道参数、太阳位置、能量需求等
        # Output: 替代子集
        sats = [n for n in topology[0] if isinstance(n, Satellite)]
        gss = [n for n in topology[1] if isinstance(n, GroundStation)]
        # 1. 获取轨道周期
        cyc = sats[0].get_orbital_cycle() if sats else 0
        cyc_slot = math.ceil(cyc / sats[0].SLOT) if cyc > 0 else 0
        
        # 按轨道 ID 对卫星进行分组 (ORB_i，论文中把orbit作为不同plane的称呼，实质上一回事
        orbits: Dict[int, List[Satellite]] = {}
        for s in sats:
            p_id = s.plane # 假设 Satellite 对象有 orbit_id 属性
            if p_id not in orbits: orbits[p_id] = []
            orbits[p_id].append(s)
            
        orbit_ids = list(orbits.keys())
        M = len(orbit_ids)
        
        # 2. 筛选在当前周期内到达的任务 A_s
        # A_s = {k | src_k = s, t <= T_arv <= t + cyc - 1}
        # 这里我们预处理为每个卫星的待处理任务集
        sat_tasks: Dict[str, List[Mission]] = {}
        for task in tasks:
            if t_slot <= task.start_slot <= t_slot + cyc_slot - 1:
                # 注意：task 可能是对象，使用 task.source_id
                s_id = task.src.address 
                if s_id not in sat_tasks: sat_tasks[s_id] = []
                sat_tasks[s_id].append(task)
                
        # 3. 估计每个轨道的阳光时长和任务总量
        self.sunlit = {oid: 0.0 for oid in orbit_ids}
        task_demand = {oid: 0.0 for oid in orbit_ids}
        for oid in orbit_ids:
            # 计算该轨道总阳光 (Line 5)
            # 假设 sat.is_sunlit(slot) 返回该时刻是否在阳光下
            for s in orbits[oid]:
                for tau in range(t_slot, t_slot + cyc_slot):
                    tau_time = t + tau * WORLD.SLOT
                    if s.is_sunlit(tau_time):
                        self.sunlit[oid] += 1
                        
            # 计算该轨道总任务量 (Line 6)
            for s in orbits[oid]:
                tasks_in_s = sat_tasks.get(s.id, [])
                # 假设 Mission.comp_demand 表示 T_cp
                for tk in tasks_in_s:
                    # 计算处理所需大概时间
                    T_cp: int = math.ceil(tk.calc_total_workload()/s.processor_clock_frequency)
                    task_demand[oid] += T_cp
            
        # 4. 计算分配权重和目标差额 (Line 7-9)
        total_task = sum(task_demand.values())
        total_sunlit = sum(self.sunlit.values())
        
        target = {oid: 0.0 for oid in orbit_ids}

        if total_task > 0:
            for oid in orbit_ids:
                # 计算当前task所需时间占所有人无时间比例作为权重
                w_i = task_demand[oid] / total_task
                # target[oid] = Int(w_i * Σsunlit) - sunlit[oid]
                target[oid] = int(w_i * total_sunlit) - self.sunlit[oid]
        
        # 5. 分配轨道子集 (Line 10-18)
        # idle = {i | task[i] == 0}
        idle_orbits = [oid for oid in orbit_ids if task_demand[oid] == 0]
        alt_set: Dict[int, Set[int]] = {}

        for oid in orbit_ids:
            if target[oid] < 0:
                # 阳光富余或任务极少
                alt_set[oid] = {oid}
            else:
                # 阳光不足，调用 Knapsack 借用 idle 轨道的阳光
                subset = self._knapsack(idle_orbits, self.sunlit, target[oid])
                alt_set[oid] = {oid}.union(set(subset))
                
                # 从 idle 池中移除已分配的轨道 (Line 18)
                for used_oid in subset:
                    idle_orbits.remove(used_oid)

        return alt_set
    
    def _get_available_gs(self, s: "Satellite", t_slot: int) -> Tuple[Link, int]:
        """寻找当前与卫星有链路且最早可用的地面站"""
        visible_dl = [n for n in s.connections if isinstance(n.dst, GroundStation)]
        # visible_gss = [n.dst for n in visible_dl]
        if not visible_dl:
            return None, 0
        # 简单逻辑：找一个空闲时间最早的地面站
        best_dl = min(visible_dl, key=lambda dl: self._gs_available_time(dl, t_slot))
        return best_dl, self._gs_available_time(best_dl, t_slot)
    
    def _gs_available_time(self, dl: "Link", t_slot: int) -> int:
        _available_cap = dl.capacity - sum(p.processed_vol for p in dl.processes)
        if _available_cap > 0:
            return t_slot
        else:
        # 计算传输所需剩余时间
            min_slot = min(dl.processes, key=lambda p: p.time_cost())
            return t_slot + min_slot
    
    def _orbit_based_offloading(self, src_sat: "Satellite", new_arrival_task: "Mission", current_slot: int, alt_set: Dict[int, Set[int]]) -> Tuple[int, dict]:
        """
        复现 Algorithm 2: Orbit-based Offloading
        """
        # 1. 尝试卸载到地面站 (Line 1-5)
        # 获取当前可见且可用的地面站
        dl, t_gs = self._get_available_gs(src_sat, current_slot)
        if dl:
            # 计算传输延迟: z_k / Cap(src, gs)
            # z_k 是任务数据大小, Cap 是链路容量
            _available_cap = dl.capacity - sum(p.processed_vol for p in dl.processes)
            trans_delay = new_arrival_task.data_size / _available_cap
            if t_gs + trans_delay <= new_arrival_task.deadline:
                # 更新地面站可用时间并返回
                # self.gs_available_time[dl.id] = t_gs + trans_delay
                return dl.id, None # dst_k = gs

        # 2. 尝试本地处理 (Line 6-8)
        # 调用之前复现的 Algorithm 3 (Arrange 函数)
        # 注意：这里需要把当前任务加入到卫星现有的任务队列中进行模拟调度
        # temp_task_list = src_sat.get_pending_tasks() + [new_arrival_task]
        temp_task_list = [m for m in WORLD.missions if m.position.address == src_sat.address and not m.status == MissionStatus.COMPLETE]
        X_hat, flag_sun = self._processing_arrangement(src_sat, current_slot, temp_task_list)
        
        if flag_sun == 1:
            # 本地阳光充足，直接本地处理
            return src_sat.id, X_hat

        # 3. 卸载到其他轨道/卫星 (Line 9-15)
        # 寻找负荷/阳光比例最小的轨道 (Line 12)
        # i = arg min_{j in alt_set} cnt[j] / sunlit[j]
        cnt: Dict[int, int] = {}
        for s in WORLD.satellites:
            p_id = s.plane # 假设 Satellite 对象有 orbit_id 属性
            if p_id not in cnt: cnt[p_id] = sum(p.time_cost() for p in s.processes)
        
        best_orbit_id = -1
        min_ratio = float('inf')
        
        for j in alt_set:
            # 防止除以 0
            sun_val = self.sunlit.get(j, 1)
            load_val = cnt.get(j, 0)
            ratio = load_val / sun_val
            if ratio < min_ratio:
                min_ratio = ratio
                best_orbit_id = j
        
        # 更新该轨道的任务计数器 (Line 13)
        cnt[best_orbit_id] = cnt[best_orbit_id] + \
            new_arrival_task.calc_total_workload() / src_sat.processor_clock_frequency
        
        # 在选定的轨道内寻找能量最高的卫星 (Line 14-15)
        # dst_k = arg max_{s in ORB_i} E[s]
        orbit_sats = [s for s in WORLD.satellites if s.plane == best_orbit_id]
        E = {s.address: self._query_energy(s) for s in orbit_sats}
        dst_k_address: str = max(E, key=E.get)
        
        # 4. 如果最终确定的目标是自己，确认调度表 (Line 16-17)
        if dst_k_address == src_sat.id:
            return src_sat.id, X_hat
            
        return dst_k_address, None
    
    def _query_energy(self, s: "Satellite") -> float:
        """查询卫星当前的能量状态"""
        cyc = s.get_orbital_cycle()
        cyc_slot = math.ceil(cyc / WORLD.SLOT)
        e = s.power_of_solar_panel * s.sunlit_slots_in_period(s.get_orbital_cycle, cyc_slot) * WORLD.SLOT +\
             s.battery_level - s.power_of_computing * sum(p.time_cost() for p in s.processes) * WORLD.SLOT 
        return e
    
    def _processing_arrangement(self, s: Satellite, t: Time, t_slot: int, K_s: List[Mission]):
        """根据卫星当前的处理能力和任务需求，动态调整任务的处理顺序和资源分配，以提升整体性能。"""
        # 1. Sort(Ks) based on T_ddl in ascending order
        sorted_tasks = sorted(K_s, key=lambda x: x.deadline)
        n = len(sorted_tasks)
        
        # 初始化 T_latest 数组
        t_latest = [0] * n
        
        # 2. 逆向计算每个任务的最晚启动时间
        # 最后一个任务：T_latest = T_ddl - T_cp
        t_latest[n-1] = sorted_tasks[n-1].deadline - \
            math.ceil(sorted_tasks[n-1].calc_total_workload()/s.processor_clock_frequency)
        
        # 倒序循环：T_latest^k = min(T_ddl^k, T_latest^{k+1}) - T_cp^k
        for k in range(n - 2, -1, -1):
            t_latest[k] = min(sorted_tasks[k].deadline, t_latest[k+1]) - \
                math.ceil(sorted_tasks[k].calc_total_workload()/s.processor_clock_frequency)
                
        # 3. 正序安排处理时间
        flag_sun = 1
        t_earliest_val = t_slot
        t_earliest = t
        X = {} # 存储每个任务的起始 slot
        
        for k in range(n):
            task = sorted_tasks[k]
            
            # 搜索下一个日照时刻 T_sunlit
            # 寻找满足 sun_{s, tau} = 1 且 tau >= T_earliest 的最小值
            t_sunlit = self._find_next_sunlit_slot(s, t_earliest, t_earliest_val)
            
            # 判定执行策略 (Line 5-8)
            if t_sunlit <= t_latest[k]:
                # 可以在阳光下执行，安排在 T_sunlit 开始
                start_time = t_sunlit
            else:
                # 阳光来得太晚，为了保住 Deadline，必须在 T_latest 强行开始
                start_time = t_latest[k]
                flag_sun = 0  # 标记使用了电池（非阳光环境）
            
            # 记录任务 k 的安排结果
            X[task.id] = start_time
            
            # 更新下一个任务的最早可用时间 (Line 9)
            # T_earliest^{k+1} = start_time + T_cp^k
            t_earliest_val = start_time + \
                math.ceil(task.calc_total_workload()/s.processor_clock_frequency)
                
        return X, flag_sun