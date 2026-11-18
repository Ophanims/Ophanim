from simulator.core.model import SampledModel
from datetime import datetime
from typing import List
import numpy as np
from pydantic import BaseModel
from simulator.schemas.base import SnapshotModel
from typing import Any
from simulator.schemas.base import XYZ, LatLon

class ROISnapshot(SnapshotModel):
    id: str
    corners_pos: List[XYZ]
    corners_loc: List[LatLon]
    centre_pos: XYZ
    centre_loc: LatLon

class ROIEntity(SampledModel):
    def __init__(self, time_series: dict[str, Any], ):
        self.time_series: dict[str, Any] = time_series
        self.id: str = time_series['id']
        self.length: float = time_series['roi_length']
        self.centre_pos: XYZ = XYZ(x=0.0, y=0.0, z=0.0)  # ECEF坐标
        self.centre_loc: LatLon = LatLon(lat=0.0, lon=0.0)  # 地理坐标（纬度，经度）
        self.corners_pos: List[XYZ] = []
        self.corners_loc: List[LatLon] = []

    # 1.1. 位置坐标条件
    def _at(self, period_counter: int, slot_counter: int):
        pos = self.time_series["center_xyz"][period_counter]
        self.centre_pos = XYZ(x=pos[0], y=pos[1], z=pos[2])

        lat, lon = self.time_series["center_latlon"]
        self.centre_loc = LatLon(lat=lat, lon=lon)

        self.corners_pos = [XYZ(x=corner[0], y=corner[1], z=corner[2]) for corner in self.time_series["target_corners_xyz"][period_counter]]
        self.corners_loc = [LatLon(lat=corner[0], lon=corner[1]) for corner in self.time_series["target_corners_latlon"]]

    def tick(self, period_counter: int, slot_counter: int):
        """
        更新ROI的状态
        :param t: 当前时间
        """
        self._at(period_counter, slot_counter)

    def snapshot(self) -> ROISnapshot:
        """
        返回ROI的快照
        :return: 快照字典
        """
        return ROISnapshot(
            id=self.id,
            corners_pos=self.corners_pos,
            corners_loc=self.corners_loc,
            centre_pos=self.centre_pos,
            centre_loc=self.centre_loc
        )

    def serialize(self) -> dict:
        return self.snapshot().model_copy(deep=True).model_dump(mode="json")


