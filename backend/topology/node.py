from typing import Any, List, TYPE_CHECKING

from entity.entity import Entity
from entity.process import Process

if TYPE_CHECKING:
    from topology.link import Link
    from entity.mission import Mission

class Node(Entity):

    def __init__(self, type: str):
        super().__init__(type=type)
        
        self.connections: List["Link"] = []
        self.missions: List["Mission"] = []
        
        # 模拟
        self.processes: List[Process] = []  # 当前链路上正在进行的传输过程列表
         
         
    def list_connection_addresses(self) -> List[str]:
        """返回当前连接的节点地址列表"""
        return [l.dst.address for l in self.connections]