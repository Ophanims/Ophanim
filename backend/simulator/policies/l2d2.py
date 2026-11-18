from simulator.policies.base import SchedulingPolicy
from simulator.policies.commands import finish_planning
from simulator.entities.station_entity import StationEntity
from simulator.services.network_service import LinkSnapshot
from typing import List, Tuple
import numpy as np


class L2D2Policy(SchedulingPolicy):
    def __init__(self):
        self._prev_perm = None

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


    def decide_actions(self):
        for node in self.sat:
            node.clear_indicators()
        ages = {task.id: task.t_end for task in self.task_manager.tasks}
        # 初始化数值
        trans_reqs = []


        # 获取当前任务和节点状态

        tasks = self.task_manager.get_tasks_at(step=self.frame_counter)

        # 初始化状态管理器和决策管理器的活跃任务数

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

        return finish_planning(self, trans_reqs, ages)
