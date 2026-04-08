from backend.model.node import Node, NodeConfig
from skyfield.api import wgs84
from skyfield.timelib import Time

class GroundStation():
    def __init__(self, id: int, lon: float, lat: float, alt: float):
        
        self.id: int = id
        
        # 地理坐标
        self.lat: float = 0.0
        self.lon: float = 0.0
        self.alt: float = 0.0  # 高度 (m)
        
        # ECEF 坐标
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0
        
        # 通信属性
        self.TRANSMIT_ANTENNA_GAIN: float = 0.0  # 发射天线增益
        self.RECEIVE_ANTENNA_GAIN: float = 0.0   # 接收天线增益
        self.TRANSMIT_SIGNAL_POWER: float = 0.0  # 发射信号功率

    def update(self, t: Time):
        # 更新 ECEF 坐标
        topos = wgs84.latlon(self.lat, self.lon)
        geocentric = topos.at(t)
        self.x, self.y, self.z = geocentric.position.m

    def get_state(self):
        state = super().get_state()
        state.update({
            "type": "ground_station",
            "connected_count": len(self.connected_sats)
        })
        return state