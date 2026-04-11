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
        self.CARRIER_FREQUENCY_OF_UP: float = 0.0
        self.CARRIER_FREQUENCY_OF_DL: float = 0.0
        self.BANDWIDTH_OF_UL: float = 0.0
        self.BANDWIDTH_OF_DL: float = 0.0
        # self.ANTENNA_GAIN_OF_UL_RECEIVE: float = 0.0   # 接收天线增益
        self.ANTENNA_GAIN_OF_UL_TRANSMIT: float = 0.0  # 发射天线增益
        self.ANTENNA_GAIN_OF_DL_RECEIVE: float = 0.0   # 接收天线增益
        # self.ANTENNA_GAIN_OF_DL_TRANSMIT: float = 0.0  # 发射天线增益
        self.UL_TRANSMIT_ANTENNA_GAIN: float = 0.0
        self.DL_RECEIVE_ANTENNA_GAIN: float = 0.0
        self.FACTOR_OF_TRANSMISSION_ENERGY: float = 0.0
        self.EFFICIENCY_OF_TARGET_SPECTRUM: float = 0.0
        self.MAXIMUM_CONCURRENT_TRANSMISSION: int = 0
        self.EFFICIENCY_OF_POWER_AMPLIFIER: float = 0.0
        self.STATIC_POWER_OF_UP_TRANSMITTING: float = 0.0  # 传输静态功率
        
        self.transmit_signal_UL_power: float = 0.0  # 发射信号功率
        self.power_of_UL_transmission: float = 500  # 传输动态功率（W）
        
        # 状态
        self.onUpload: bool = False
        self.onDownload: bool = False
        
    def setup(self, project):
        self.CARRIER_FREQUENCY_OF_UP = float(project.carrierFrequencyOfUpGhz or 0.0)
        self.CARRIER_FREQUENCY_OF_DL = float(project.carrierFrequencyOfDlGhz or 0.0)
        self.BANDWIDTH_OF_UL = float(project.bandwidthOfUlMhz or 0.0)
        self.BANDWIDTH_OF_DL = float(project.bandwidthOfDlMhz or 0.0)
        self.ANTENNA_GAIN_OF_UL_TRANSMIT = float(project.antennaGainOfUlTransmitDbi or 0.0)
        self.ANTENNA_GAIN_OF_DL_RECEIVE = float(project.antennaGainOfDlReceiveDbi or 0.0)
        self.FACTOR_OF_TRANSMISSION_ENERGY = float(project.factorOfTransmissionEnergy or 0.0)
        self.EFFICIENCY_OF_TARGET_SPECTRUM = float(project.efficiencyOfTargetSpectrum or 0.0)
        self.MAXIMUM_CONCURRENT_TRANSMISSION = int(project.maximumConcurrentTransmission or 0)
        self.EFFICIENCY_OF_POWER_AMPLIFIER = float(project.efficiencyOfPowerAmplifier or 0.0)
        self.STATIC_POWER_OF_UP_TRANSMITTING = float(project.staticPowerOfUplinkTransmittingW or 0.0)

    def tick(self, t: Time):
        # 更新 ECEF 坐标
        topos = wgs84.latlon(self.lat, self.lon, self.alt)
        geocentric = topos.at(t).position.m
        self.x, self.y, self.z = geocentric
        self.transmit_signal_UL_power = self.calc_transmit_signal_power()
        
    def calc_transmit_signal_power(self) -> float:
        # 简化模型：假设发射功率与带宽成正比
        result = self.EFFICIENCY_OF_POWER_AMPLIFIER * (self.power_of_UL_transmission - self.STATIC_POWER_OF_UP_TRANSMITTING)
        return max(result, 0.0)

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