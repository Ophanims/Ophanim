from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

# --- 1. 状态定义 ---
class NodeStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# 1. 基础属性定义
class NodeConfig(BaseModel):
    id: str
    name: str
    # 地理坐标
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0  # 高度 (m)
    # ECEF 坐标
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

# 2. 抽象基类
class Node(ABC):
    def __init__(self, config: NodeConfig):
        self.id = config.id
        self.name = config.name
        self.status = NodeStatus.ACTIVE
        
        self.geographic_coordinates = {"lat": config.lat, "lon": config.lon, "alt": config.alt}
        self.cartesian_coordinates = {"x": config.x, "y": config.y, "z": config.z}
        
        self.transmit_antenna_gain: float = 0.0  # 发射天线增益
        self.receive_antenna_gain: float = 0.0   # 接收天线增益
        self.transmit_signal_power: float = 0.0  # 发射信号功率

    @abstractmethod
    def update(self, dt: float, global_time: float):
        """
        每个节点必须实现自己的更新逻辑
        dt: 步长
        global_time: 当前仿真绝对时间
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """返回用于前端渲染的状态字典"""
        return {
            "id": self.id,
            "pos": self.geographic_coordinates,
            "status": self.status,
            "buffer": self.data_buffer
        }