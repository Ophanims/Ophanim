import math
from typing import Dict, List, Set, Tuple

from algorithm.algo import Algorithm
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
        sunlit = {oid: 0.0 for oid in orbit_ids}
        task_demand = {oid: 0.0 for oid in orbit_ids}
        for oid in orbit_ids:
            # 计算该轨道总阳光 (Line 5)
            # 假设 sat.is_sunlit(slot) 返回该时刻是否在阳光下
            for s in orbits[oid]:
                for tau in range(t_slot, t_slot + cyc_slot):
                    tau_time = t + tau * WORLD.SLOT
                    if s.is_sunlit(tau_time):
                        sunlit[oid] += 1
                        
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
        total_sunlit = sum(sunlit.values())
        
        target = {oid: 0.0 for oid in orbit_ids}

        if total_task > 0:
            for oid in orbit_ids:
                # 计算当前task所需时间占所有人无时间比例作为权重
                w_i = task_demand[oid] / total_task
                # target[oid] = Int(w_i * Σsunlit) - sunlit[oid]
                target[oid] = int(w_i * total_sunlit) - sunlit[oid]
        
        # 5. 分配轨道子集 (Line 10-18)
        # idle = {i | task[i] == 0}
        idle_orbits = [oid for oid in orbit_ids if task_demand[oid] == 0]
        alt_set: Dict[int, Set[int]] = {}

        # 按照 Algorithm 1 的逻辑遍历
        for oid in orbit_ids:
            if target[oid] < 0:
                # 阳光富余或任务极少
                alt_set[oid] = {oid}
            else:
                # 阳光不足，调用 Knapsack 借用 idle 轨道的阳光
                subset = self._knapsack(idle_orbits, sunlit, target[oid])
                alt_set[oid] = {oid}.union(set(subset))
                
                # 从 idle 池中移除已分配的轨道 (Line 18)
                for used_oid in subset:
                    idle_orbits.remove(used_oid)

        return alt_set
    
    def _orbit_based_offloading(self):
        """根据卫星当前轨道位置，智能选择任务卸载到地面站或其他卫星，以优化通信效率和能量消耗。"""
        pass
    
    def _processing_arrangement(self):
        """根据卫星当前的处理能力和任务需求，动态调整任务的处理顺序和资源分配，以提升整体性能。"""
        pass
    
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