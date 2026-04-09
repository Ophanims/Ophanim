from pydantic import BaseModel

from entity.entity import Entity, EntityType
from skyfield.api import wgs84
from skyfield.timelib import Time

class GroundStationSnapshot(BaseModel):
    addr: str
    type: str
    name: str
    x: float
    y: float
    z: float
    lat: float
    lon: float
    alt: float
    onUpload: bool
    onDownload: bool

class GroundStation(Entity):
    def __init__(self, name: str, lon: float, lat: float, alt: float):
        super().__init__(type=EntityType.GS)
        
        self.name: str = name
        
        # 地理坐标
        self.lat: float = lat
        self.lon: float = lon
        self.alt: float = alt  # 高度 (m)
        
        # ECEF 坐标
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0
        
        # 通信属性
        self.TRANSMIT_ANTENNA_GAIN: float = 0.0  # 发射天线增益
        self.RECEIVE_ANTENNA_GAIN: float = 0.0   # 接收天线增益
        self.TRANSMIT_SIGNAL_POWER: float = 0.0  # 发射信号功率
        
        # 状态
        self.onUpload: bool = False
        self.onDownload: bool = False
        
    def setup(self, project):
        self.TRANSMIT_ANTENNA_GAIN = project.transmitAntennaGain
        self.RECEIVE_ANTENNA_GAIN = project.receiveAntennaGain
        self.TRANSMIT_SIGNAL_POWER = project.transmitSignalPower

    def tick(self, t: Time):
        # 更新 ECEF 坐标
        topos = wgs84.latlon(self.lat, self.lon, self.alt)
        geocentric = topos.at(t).position.m
        self.x, self.y, self.z = geocentric

    def snapshot(self) -> GroundStationSnapshot:
        return GroundStationSnapshot(
            addr=self.address,
            type=self.type,
            name=self.name,
            x=self.x,
            y=self.y,
            z=self.z,
            lat=self.lat,
            lon=self.lon,
            alt=self.alt,
            onUpload=self.onUpload,
            onDownload=self.onDownload
        )
        
    def serialize(self) -> dict:
        return self.snapshot().model_dump()