from typing import Any, List, TYPE_CHECKING

from entity.entity import Entity

if TYPE_CHECKING:
    from entity.link import Link
    from entity.mission import Mission

class Node(Entity):

    def __init__(self, type: str):
        super().__init__(type=type)
        
        self.connections: List["Link"] = []
        self.missions: List["Mission"] = []
         
         
    def list_connection_addresses(self) -> List[str]:
        """返回当前连接的节点地址列表"""
        return [l.dst.address for l in self.connections]