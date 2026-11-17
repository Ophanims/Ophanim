# from datetime import datetime
# import uuid
# from simulator.entities._satellite_modules.constants import E_C_T, E_D, R_DL, R_T
# from simulator.entities.pipe_entity import PipeEntity
# from simulator.snapshots.msg_dto import Message, MessageStatus, MessageType

# class CommunicationModule:
#     def _send(self, receiver: str, receiver_type: str, msg: Message, pipe: PipeEntity, t: datetime, dt: float):
#         self.theta_t = True
#         _m = Message(
#             id=msg.id,
#             sender=self.id,
#             senderType="SAT",
#             receiver=receiver,
#             receiverType=receiver_type,
#             type=msg.type,
#             size=msg.size,
#             targetId=msg.targetId,  # 目标ID
#             targetLoc=msg.targetLoc,  # 目标位置
#             targetLen=msg.targetLen,  # 目标长度
#             ts=t,
#             status=msg.status
#         )
#         pipe.forward(msg=_m, t_send=t, t_delay=dt)

#     def _broadcast(self, links, msg, pipe, t, dt, receiver_type):
#         for link in links:
#             dst = link.dst if link.dst != self.id else link.src
#             self._send(receiver=dst, receiver_type=receiver_type, msg=msg, pipe=pipe, t=t, dt=dt)

#     def _distribute_isl_message(self, msg: Message, t: datetime, dt: float, pipe: PipeEntity):
#         if msg is None:
#             return
#         isl_links = [link for link in self.j if link.type == 'ISL']
#         if not isl_links:
#             return
#         self._broadcast(isl_links, msg, pipe, t, dt, "SAT")

#     def _relay_payload(self, type: MessageType, t: datetime, dt: float, pipe: PipeEntity):
#         # 如果卫星不处于地面站通信状态，则跳过。
#         if not self.on_gs_t:
#             return
#         # 如果卫星处于地面站通信状态，则尝试将数据发送到地面站。
#         # 获取所有地面站通信链路。
#         links = [link for link in self.j if link.type == 'DL']
#         # 如果没有地面站通信链路，则跳过。
#         if not links:
#             return
#         # 计算剩余数据量和传输能力。
#         pending_data_vol = self.y_buff if type == MessageType.Y else self.z_buff
#         # 如果没有待传输数据，则跳过。
#         if pending_data_vol <= 0:
#             return
#         # 计算总传输速率。
#         total_rate = sum(link.rate for link in links)
#         # 计算已完成下传的传输量
#         prev_trans = self.psi_t * self.r if type == MessageType.Y else self.phi_t
#         # 计算本次传输能力（去掉已完成下传的传输量后）
#         trans_cap = total_rate * dt - prev_trans
#         # 开始遍历每个地面站通信链路，计算每个链路的传输量。
#         for link in links:
#             # 计算每个链路的传输比例和传输量。
#             allocation_ratio = link.rate / total_rate if total_rate > 0 else 0
#             per_link = min(pending_data_vol * allocation_ratio, trans_cap * allocation_ratio)
#             # 确定接收方。
#             # 如果是通信，则接收方不能是本卫星。
#             dst = link.dst if link.dst != self.id else link.src
#             send_data_vol = min(per_link, pending_data_vol)
#             send_data_vol_unpressed = send_data_vol if type == MessageType.Y else send_data_vol / self.r
#             energy_needed = self.calculate_rf_energy(data_bits=send_data_vol, rate_bps=link.rate)
#             if not self._can_execute(energy_needed):
#                 continue
#             self._execute(energy_needed)
#             if type == MessageType.Y:
#                 self.y_buff -= send_data_vol
#                 self.phi_t += send_data_vol_unpressed
#             else:
#                 self.z_buff -= send_data_vol
#                 self.psi_t += send_data_vol_unpressed
#             self.theta_t = True
#             msg = Message(
#                 id=uuid.uuid4().hex,
#                 sender=self.id,
#                 senderType="SAT",
#                 receiver=dst,
#                 receiverType="GS",
#                 type=type,
#                 # 传给地面站的数据量是未压缩的，
#                 # 这样地面站不需要再进行转换。
#                 size=send_data_vol_unpressed,
#                 ts=t,
#                 status=MessageStatus.PENDING
#             )
#             self._send(receiver=dst, receiver_type="GS", msg=msg, pipe=pipe, t=t, dt=dt)

#     def _isl_payload(self, type: MessageType, t: datetime, dt: float, pipe: PipeEntity):
#         if self.on_gs_t and self.y_buff < 1 and self.z_buff < 1:
#             return
#         links = [link for link in self.j if link.type == 'ISL']
#         if not links:
#             return
#         # 计算剩余数据量和传输能力。
#         pending_data_vol = self.y_buff if type == MessageType.Y else self.z_buff
#         # 如果没有待传输数据，则跳过。
#         if pending_data_vol <= 0:
#             return
#         # 计算总传输速率。
#         total_rate = sum(link.rate for link in links)
#         # 计算已完成下传的传输量
#         prev_trans = self.y_ij_t * self.r if type == MessageType.Y else self.z_ij_t
#         trans_cap = total_rate * dt - prev_trans
#         for link in links:
#             allocation_ratio = link.rate / total_rate if total_rate > 0 else 0
#             per_link = min(pending_data_vol * allocation_ratio, trans_cap * allocation_ratio)
#             dst = link.dst if link.dst != self.id else link.src
#             send_data_vol = min(per_link, pending_data_vol)
#             send_data_vol_unpressed = send_data_vol if type == MessageType.Y else send_data_vol / self.r
#             energy_needed = self.calculate_isl_energy(data_bits=send_data_vol, rate_bps=link.rate)
#             if not self._can_execute(energy_needed):
#                 continue
#             self._execute(energy_needed)
#             if type == MessageType.Y:
#                 self.y_buff -= send_data_vol
#                 self.y_ij_t_list.append(send_data_vol_unpressed)
#                 self.y_ij_t += send_data_vol_unpressed
#             else:
#                 self.z_buff -= send_data_vol
#                 self.z_ij_t_list.append(send_data_vol_unpressed)
#                 self.z_ij_t += send_data_vol_unpressed
#             self.theta_t = True
#             msg = Message(
#                 id=uuid.uuid4().hex,
#                 sender=self.id,
#                 senderType="SAT",
#                 receiver=dst,
#                 receiverType="SAT",
#                 type=type,
#                 size=send_data_vol,
#                 ts=t,
#                 status=MessageStatus.PENDING
#             )
#             self._send(receiver=dst, receiver_type="SAT", msg=msg, pipe=pipe, t=t, dt=dt)
