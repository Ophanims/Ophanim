from datetime import datetime
import numpy as np
from pydantic import BaseModel
from simulator.schemas.base import SnapshotModel
from typing import Any
from simulator.schemas.base import XYZ

class SunSnapshot(SnapshotModel):
    id: str
    pos: XYZ

class SunEntity:
    def __init__(self, time_series: dict[str, Any], ):
        self.time_series: dict[str, Any] = time_series  # 卫星
        self.id: str = time_series['id']
        self.pos: XYZ = XYZ(x=0.0, y=0.0, z=0.0)
        self.rotation: float = 0.0  # 地球自转角度

    # 1.1. 位置坐标条件
    def _at(self, period_counter: int, slot_counter: int):
        pos = self.time_series["xyz"][period_counter]
        self.pos = XYZ(x=pos[0], y=pos[1], z=pos[2])

    def tick(self, period_counter: int, slot_counter: int):
        self._at(period_counter, slot_counter)

    def snapshot(self) -> SunSnapshot:
        return SunSnapshot(
            id=self.id,
            pos=self.pos,
        )

    def serialize(self) -> dict:
        return self.snapshot().model_copy(deep=True).model_dump(mode="json")


