# from datetime import datetime
# from simulator.entities._satellite_modules.constants import BUFFER_MAX
# from simulator.entities.pipe_entity import PipeEntity
# from simulator.services.mission_service import MissionService
# from simulator.snapshots.msg_dto import Message, MessageStatus


# class MessageHandlingModule:
#     def receive(self, incoming_msg: Message):
#         existing_msg = next((m for m in self.acts if m.id == incoming_msg.id), None)
#         if existing_msg is None:
#             self.acts.append(incoming_msg)
#         else:
#             if incoming_msg.status > existing_msg.status:
#                 existing_msg.status = incoming_msg.status

#     def _process_message_sync(self, t_dt: datetime, dt: float, pipe: PipeEntity, ms: MissionService):
#         # Iterate over a copy to allow safe removal during iteration
#         self.y_ji_t_list.clear()
#         self.z_ji_t_list.clear()
#         for msg in self.acts[:]:
#             if msg.type == 0:
#                 if msg.status == MessageStatus.SNAP:
#                     if self.attn and msg.id == self.attn.id:
#                         self.attn = None
#                     self._distribute_isl_message(msg, t_dt, dt, pipe)
#                     msg.status = MessageStatus.DISCARD
#                 elif msg.status == MessageStatus.PENDING:
#                     self._distribute_isl_message(msg, t_dt, dt, pipe)
#                     msg.status = MessageStatus.PROCESSING
#             # 处理接收到的y消息
#             elif msg.type == 1:
#                 if msg.status == MessageStatus.PENDING:
#                     _size = msg.size
#                     if _size > 0:
#                         fill_raw = min(_size, BUFFER_MAX - self.y_buff)
#                         self.y_ji_t_list.append(fill_raw)
#                         self.y_ji_t += fill_raw
#                         # self.y_ji_t += fill_raw
#                         self.y_buff += fill_raw
#                         _size -= fill_raw
#                         self.loss += _size  # Record lost raw data
#                     msg.status = MessageStatus.DONE
#                 if msg.status == MessageStatus.DONE:
#                     self.acts.remove(msg)
#             # 处理接收到的z消息
#             elif msg.type == 2:
#                 if msg.status == MessageStatus.PENDING:
#                     _size = msg.size
#                     if _size > 0:
#                         fill_proc = min(_size, BUFFER_MAX - self.z_buff)
#                         self.z_ji_t_list.append(fill_proc / self.r)
#                         self.z_ji_t += fill_proc / self.r
#                         # self.z_ji_t += fill_proc
#                         self.z_buff += fill_proc
#                         _size -= fill_proc
#                         self.loss += _size / self.r
#                     msg.status = MessageStatus.DONE
#                 if msg.status == MessageStatus.DONE:
#                     self.acts.remove(msg)
