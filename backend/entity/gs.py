from typing import List

import numpy as np
from pydantic import BaseModel

from entity.node import Node
from util.time_utils import skyfield_to_datetime
from entity.mission import Mission
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
    connections: List[str]

class GroundStation(Node):
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
        
        # 仿真参数
        self.RNG: np.random.Generator = np.random.default_rng()
        self.SLOT: float = 0.0  # 时间步长 (秒)
        
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
        self.RNG = np.random.default_rng(getattr(project, "seed", None))
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
        
        # _now = skyfield_to_datetime(t).isoformat()
        # _applied_missions = self.generate_missions(now=_now)
        
        # self.missions.extend(_applied_missions)
        
    def execute(self):
        # if len(self.missions) > 0:
        pass
        
    def generate_missions(self, now: str) -> List[Mission]:
        # 根据泊松分布和SEED生成新的Mission
        lam = 0.2 * self.SLOT
        num_missions = self.RNG.poisson(lam)
        missions = []
        for i in range(num_missions):
            mission = Mission(
                position=self.address,
                start_time=now,
            )

            missions.append(mission)

        return missions
        
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
            onDownload=self.onDownload,
            connections=self.list_connection_addresses(),
        )
        
    def serialize(self) -> dict:
        return self.snapshot().model_dump()