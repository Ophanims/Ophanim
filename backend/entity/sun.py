from pydantic import BaseModel

from core.simulation_clock import CLOCK
from util.const import EARTH, SUN
from entity.entity import Entity, EntityType
from skyfield.api import wgs84
from skyfield.timelib import Time

class SunSnapshot(BaseModel):
    addr: str
    type: str
    x: float
    y: float
    z: float

class Sun(Entity):
    def __init__(self):
        super().__init__(type=EntityType.SUN)
        
        # ECEF 坐标
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0

    def tick(self):
        # 更新 ECEF 坐标
        ast_sun = EARTH.at(CLOCK.current_time).observe(SUN)
        sun_ecef = ast_sun.apparent().position.m.T
        self.x, self.y, self.z = sun_ecef

    def snapshot(self) -> SunSnapshot:
        return SunSnapshot(
            addr=self.address,
            type=self.type,
            x=self.x,
            y=self.y,
            z=self.z,
        )
        
    def serialize(self) -> dict:
        return self.snapshot().model_dump()