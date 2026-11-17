# from datetime import datetime
# from simulator.entities._satellite_modules.constants import IMG_SIZE
# from simulator.entities.functions.target import is_on_target
# from simulator.snapshots.mission_ss import MissionStatus
# from simulator.snapshots.msg_dto import MessageStatus
# from simulator.models.roi_model import ROIModel

# class ImageryModule:
#     def _get_focus(self):
#         roi_id = self.attn.id
#         roi_loc = self.attn.targetLoc
#         roi_len = self.attn.targetLen
#         return ROIModel(
#             id=roi_id,
#             lat=roi_loc.lat,
#             lon=roi_loc.lon,
#             length=roi_len,
#             width=roi_len,
#         )

#     def _update_attention(self, ms: MissionService, t_dt: datetime):
#         """Update self.attn to the next PROCESSING message if not set."""
#         if not self.attn:
#             self.attn = next((m for m in self.acts if m.status == MessageStatus.PROCESSING), None)
#             ms.switch_mission_status(self.attn.id, MissionStatus.ACQUIRING, t_dt) if self.attn else None

#     def _process_attention(self, t_dt, dt, pipe, ms: MissionService):
#         """Process attention if available and on ROI."""
#         self._update_attention(ms, t_dt)
#         if self.attn:
#             roi = self._get_focus()
#             self.on_roi_t = is_on_target(
#                 sub_lat=self.loc.lat,
#                 sub_lon=self.loc.lon,
#                 sl=self.sl,
#                 v=self.v,
#                 roi_lat=roi.loc.lat,
#                 roi_lon=roi.loc.lon,
#                 roi_length=roi.length
#             )
#             if self.on_roi_t:
#                 self.attn.status = MessageStatus.SNAP
#                 self._distribute_isl_message(self.attn, t_dt, dt, pipe)
#                 self.attn.status = MessageStatus.DONE
#                 ms.switch_mission_status(self.attn.id, MissionStatus.DELIVERING, t_dt) if self.attn else None
#                 self.sto_t = IMG_SIZE
#                 self.alpha_t = IMG_SIZE
#                 self.attn = None
