import datetime
from typing import Any, List

from pydantic import BaseModel
from simulator.schemas.base import SnapshotModel
import numpy as np
from simulator.schemas.base import XYZ, LatLon
from simulator.services.network_service import LinkSnapshot

class StationSnapshot(SnapshotModel):
    id: str
    pos: XYZ
    loc: LatLon
    on_upload: bool
    on_download: bool

class StationEntity:
    def __init__(
        self,
        time_series: dict[str, Any],
    ):
        # === 基本参数 ===
        self.time_series: dict[str, Any] = time_series
        self.id = time_series['id']

        # === 拓扑与通信 ===
        self.connections: List[LinkSnapshot] = []

        # === 空间与方位 ===
        self.pos: XYZ = XYZ(x=0.0, y=0.0, z=0.0)  # ECEF坐标
        self.loc: LatLon = LatLon(lat=0.0, lon=0.0)  # 地理坐标（纬度，经度）

        # === Indicator 状态 ===
        self.on_download: bool = False
        self.on_upload: bool = False

        # === 存储区与活动 ===
        # self.uploading_list: List[Message] = []  # 待上传任务列表
        # self.downloading_list: List[Message] = []  # 待下载任务列表

    def tick(self, period_counter: int, slot_counter: int) -> None:
        self.on_download, self.on_upload = (False,) * 2
        self.phi_t = self.psi_t = self.omega_t = 0.0

        # 1. 更新自身位置
        self._at(period_counter, slot_counter)

    def _at(self, period_counter: int, slot_counter: int):
        pos = self.time_series["xyz"][period_counter]
        self.pos = XYZ(x=pos[0], y=pos[1], z=pos[2])
        lat, lon = self.time_series["latlon"]
        self.loc = LatLon(lat=lat, lon=lon)

    def snapshot(self) -> StationSnapshot:
        return StationSnapshot(
            id=self.id,
            pos=self.pos,
            loc=self.loc,
            on_upload=self.on_upload,
            on_download=self.on_download
        )

    def serialize(self) -> dict:
        return self.snapshot().model_copy(deep=True).model_dump(mode="json")
