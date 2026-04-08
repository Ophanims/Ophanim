import itertools
from typing import Any

from pydantic import BaseModel
from skyfield.timelib import Time

from controller.project_controller import ProjectBase

class EntityType:
    SAT = "earth_satellite"
    GS = "ground_station"
    ROI = "region_of_interest"

class Entity:
    """所有仿真逻辑（如轨道、能量、计算任务）必须继承此类"""
    _id_counter = itertools.count(1)

    def __init__(self, type: str, address: str | None = None):
        self.type: str = type  # 实体类型（如 "satellite"、"ground_station"）
        self.address: str = address or self._next_unique_id(type)

    @classmethod
    def _next_unique_id(cls, type_name: str) -> str:
        # 使用统一递增计数，确保当前进程内全局唯一。
        return f"@{next(cls._id_counter):08d}"

    def setup(self, project: ProjectBase): pass
    def tick(self, t: Time): pass
    def snapshot(self) -> BaseModel: pass
    def serialize(self) -> dict[str, Any]: pass