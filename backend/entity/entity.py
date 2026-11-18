import itertools
from typing import Any
from pydantic import BaseModel
from simulator.schemas.engine_config import EngineConfig
from simulator.core.model import SimulationModel, StepContext

class EntityType:
    SAT = "earth_satellite"
    GS = "ground_station"
    ROI = "region_of_interest"
    SUN = "the_sun"
    ETH = "the_earth"

class Entity(SimulationModel):
    """所有仿真逻辑（如轨道、能量、计算任务）必须继承此类"""


    def __init__(self, type: str):
        self.type: str = type  # 实体类型（如 "satellite"、"ground_station"）
        self.addr: str = self._next_unique_id()  # 全局唯一地址，格式为 "@00000001"
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0

    @classmethod
    def _next_unique_id(cls) -> str:
        # 使用统一递增计数，确保当前进程内全局唯一。
        from core.session_context import next_identity
        return f"@{next_identity('entity'):08d}"

    def setup(self, project: EngineConfig):
        """Entities without configurable resources need no initialization."""
    def tick(self):
        raise NotImplementedError("Entity.tick must be implemented")
    def transition(self, action, context: StepContext):
        self.tick()
        return self.snapshot()
    def snapshot(self) -> BaseModel:
        raise NotImplementedError("Entity.snapshot must be implemented")
    def serialize(self) -> dict[str, Any]:
        return self.snapshot().model_dump(mode="json")
