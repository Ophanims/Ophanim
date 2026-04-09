import numpy as np
from pydantic import BaseModel
from entity.entity import Entity, EntityType
from skyfield.api import wgs84
from skyfield.timelib import Time

class EarthSnapshot(BaseModel):
    addr: str
    type: str
    null_island_x: float
    null_island_y: float
    null_island_z: float
    rotational_angular_velocity: float

class Earth(Entity):
    def __init__(self):
        super().__init__(type=EntityType.ETH)
        
        self.timeslot_duration: float = 0.0  # 每个时间步的持续时间 (秒)

        # ECEF 坐标
        self.null_island_x: float = 0.0
        self.null_island_y: float = 0.0
        self.null_island_z: float = 0.0
        self.rotational_angular_velocity: float = 0.0
        
    def setup(self, project):
        self.timeslot_duration = project.timeSlot

    def tick(self, t: Time):
        # 更新 ECEF 坐标
        topos = wgs84.latlon(0.0, 0.0)  # Null Island
        p1 = topos.at(t).position.m
        self.null_island_x, self.null_island_y, self.null_island_z = p1
        # 地球自转角速度（ degrees per timeslot）
        if self.timeslot_duration <= 0:
            self.rotational_angular_velocity = 0.0
            return

        # Build the next Skyfield Time explicitly from TT Julian date.
        t2 = t.ts.tt_jd(t.tt + self.timeslot_duration / 86400.0)
        p2 = topos.at(t2).position.m
        # 向量夹角
        v1 = np.array(p1)
        v2 = np.array(p2)
        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        if denom == 0:
            self.rotational_angular_velocity = 0.0
            return
        cos_theta = np.dot(v1, v2) / denom
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        theta_deg = np.degrees(np.arccos(cos_theta))
        self.rotational_angular_velocity = theta_deg

    def snapshot(self) -> EarthSnapshot:
        return EarthSnapshot(
            addr=self.address,
            type=self.type,
            null_island_x=self.null_island_x,
            null_island_y=self.null_island_y,
            null_island_z=self.null_island_z,
            rotational_angular_velocity=self.rotational_angular_velocity,
        )
        
    def serialize(self) -> dict:
        return self.snapshot().model_dump()