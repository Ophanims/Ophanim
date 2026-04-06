from backend.model.node import Node, NodeConfig


class GroundStation(Node):
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.connected_sats: list = []

    def update(self, dt: float, global_time: float):
        # 地面站位置固定，主要更新通信链路状态
        # TODO: 检查哪些卫星在可见范围内
        pass

    def get_state(self):
        state = super().get_state()
        state.update({
            "type": "ground_station",
            "connected_count": len(self.connected_sats)
        })
        return state