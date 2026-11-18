from simulator.policies.base import SchedulingPolicy
from simulator.policies.commands import finish_planning
from simulator.policies.orbit_scheduler import OrbitScheduler


class PhoenixPolicy(OrbitScheduler, SchedulingPolicy):
    def decide_actions(self):
        for node in self.sat:
            node.clear_indicators()
        ages = {task.id: task.t_end for task in self.task_manager.tasks}
        # 初始化数值


        # 获取当前任务和节点状态

        tasks = self.task_manager.get_tasks_at(step=self.frame_counter)

        # 依据 Algorithm 1 生成按轨道的候选集合
        alt_set_by_orbit = self.get_alt_set()

        # 将匹配结果转换为传输/计算请求（Algorithm 2 驱动）
        for task in tasks:

            # 去重：若已完成则跳过
            if task.is_done:
                continue

            # 更新时间窗口（论文里作为DDL推进，这里简化为+1）
            task.t_end += 1

            # 去重：若已在队列中则跳过
            if any(r["task_id"] == task.id for r in self.comp_reqs) or any(r["task_id"] == task.id for r in self.trans_reqs):
                continue

            # 找到任务所在节点，没电或节点不存在则跳过
            node = next((s for s in self.sat if s.plane == task.plane_at and s.order == task.order_at), None)
            if node is None or node.battery_ratio <= 0:
                continue

            # 调用 Algorithm 2：优先地面；否则 Arrange（Algorithm 3）决定本地；否则轨道候选卸载
            dst_id, X = self._orbit_offloading(node, task, alt_set_by_orbit)

            self.logger.info(f"[STEP] frame={self.frame_counter} task_id={task.id} node_id={getattr(node, 'id', None)} battery={getattr(node, 'battery_ratio', None):.2f} charging={getattr(node, 'is_charging', None)} t_end={task.t_end} layer_id={task.layer_id} is_done={task.is_done}")
            self.logger.info(f"[SCHEDULE] task_id={task.id} node_id={node.id} dst_id={dst_id} local_proc={dst_id == node.id} X={X}")

            if dst_id == node.id:
                # 本地处理请求
                is_sat_computing_occupied = any(r["node"].id == node.id for r in self.comp_reqs)
                if node.is_processing is False and not is_sat_computing_occupied:
                    self.comp_reqs.append({
                        "task_id": task.id,
                        "node": node,
                    })
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
