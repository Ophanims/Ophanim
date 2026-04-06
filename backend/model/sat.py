from typing import Dict

from backend.model.node import Node, NodeConfig

class Satellite(Node):
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        
        self.plane = 0
        self.order = 0
        self.inclination = 0.0
        
        self.battery_level = 100.0  # 百分比
        self.is_in_sunlight = True

    def update(self, dt: float, global_time: float):
        # TODO: 调用轨道传播算法 (如 SGP4) 更新 self.position
        # TODO: 根据是否在阴影区更新 self.battery_level
        # 示例逻辑：每秒掉电
        consumption = 0.1 if self.is_in_sunlight else 0.5
        self.battery_level -= consumption * dt

    def get_state(self):
        state = super().get_state()
        state.update({
            "type": "satellite",
            "battery": round(self.battery_level, 2),
            "sunlit": self.is_in_sunlight
        })
        return state