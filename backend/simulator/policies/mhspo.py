from simulator.policies.base import SchedulingPolicy
from simulator.policies.commands import finish_planning
from typing import Dict, Tuple
import math
from simulator.policies.queue_scheduler import QueueScheduler


class MHSPOPolicy(QueueScheduler, SchedulingPolicy):
    def __init__(self):
        self.QF, self.QB = {}, {}
        self.PRED_WINDOW = 10
        self.ALPHA = 0.9
        self.KAPPA = 1e-5
        self.NODE_CAPACITY_PER_STEP = 1.0
        self.pred_load, self.pred_load_shared = {}, {}
        self.node_capacity, self.node_bottleneck, self.theta_n = {}, {}, {}
        self.V = 1.0
        self.MAX_HOPS = 2

    def initialize(self, view):
        if self.node_capacity:
            return
        self.QF = {s.id: [] for s in view.sat}
        self.QB = {s.id: [] for s in view.sat}
        self.pred_load = {s.id: [1.0] * self.PRED_WINDOW for s in view.sat}
        self.pred_load_shared = {s.id: [1.0] * self.PRED_WINDOW for s in view.sat}
        self.node_capacity = {s.id: self.NODE_CAPACITY_PER_STEP for s in view.sat}
        self.node_bottleneck = {s.id: 1.0 for s in view.sat}
        self.theta_n = {s.id: int(max(1, math.ceil(self.node_capacity[s.id] * 5))) for s in view.sat}

    def decide_actions(self):
        for node in self.sat:
            node.clear_indicators()
        ages = {task.id: task.t_end for task in self.task_manager.tasks}
        # 初始化数值


        # 获取当前任务和节点状态

        all_tasks = self.task_manager.get_tasks()
        tasks = self.task_manager.get_tasks_at(step=self.frame_counter)

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

        return finish_planning(self, self.trans_reqs, ages)
