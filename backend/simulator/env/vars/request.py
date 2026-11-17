# from pydantic import BaseModel

from simulator.schemas.task import Task
from pydantic import ConfigDict
from simulator.entities.satellite_entity import SatelliteEntity

class TransReq():
    def __init__(
        self,
        task: Task,
        src: SatelliteEntity,
        dst: SatelliteEntity,
    ):
        self.task = task
        self.src = src
        self.dst = dst

class CompReq():
    def __init__(
        self,
        task: Task,
        node: SatelliteEntity,
    ):
        self.task = task
        self.node = node


