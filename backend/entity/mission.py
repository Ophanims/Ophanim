import itertools
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel
from skyfield.timelib import Time

from status.mission_status import MissionStatus, MissionPhase
from entity.process import Process
from util.time_utils import skyfield_to_datetime

if TYPE_CHECKING:
    from topology.node import Node

class MissionSnapshot(BaseModel):
    id: int
    status: str
    position: str
    inference_layer: int
    data_size: float
    workload: float
    start_time: str
    end_time: str
    deadline: str

class Mission():
    _id_counter = itertools.count(1)
    def __init__(self, position: "Node", start_time: Any, start_slot: int):
        self.id = self._next_unique_id()
        self.status = MissionStatus.IDLE
        self.phase = MissionPhase.UPLOADING
        self.src = position
        
        self.IMAGE_WIDTH_PX = 10000
        self.IMAGE_HEIGHT_PX = 10000
        self.BITS_PER_CHANNEL = 8
        self.CHANNEL_PER_PIXEL = 3
        self.MAXIMUM_INFERENCE_LAYER = 7
        self.INITIAL_DATA_SIZE_MB = self.calc_image_data_size_mb()
        
        self.position = position
        self.inference_layer = 0
        self.data_size = self.INITIAL_DATA_SIZE_MB
        self.workload = self.calc_total_workload()
        self.start_time = start_time
        self.start_slot = start_slot
        self.end_time = ""
        self.deadline = ""
        
    @classmethod
    def _next_unique_id(cls) -> str:
        # 使用统一递增计数，确保当前进程内全局唯一。
        return next(cls._id_counter)
        
    def create(self, w_px: int, h_px: int, bpc: int, cpp: int):
        self.IMAGE_WIDTH_PX = w_px
        self.IMAGE_HEIGHT_PX = h_px
        self.BITS_PER_CHANNEL = bpc
        self.CHANNEL_PER_PIXEL = cpp
        
        self.data_size = self.calc_image_data_size_mb()
        
    def to_transmit(self, target: "Node", processed_vol: float) -> Process:
        self.status = MissionStatus.TRANSMITTING
        def done() -> None:
            self.done_transmit(target=target)

        _transmitted_data_size = self.data_size
        _new_process = Process(
            id=self.id, 
            name=f"Transmitting_{self.id}", 
            arrival_time=0, 
            terminal_time=None, 
            deadline=None, 
            required_vol=_transmitted_data_size,
            processed_vol=processed_vol,
            callback=done,
            )
        return _new_process
    
    def done_transmit(self, target: "Node") -> None:
        self.position = target
        self.status = MissionStatus.IDLE
        
    def to_compute(self, target: int, processed_vol: float) -> Process:
        self.status = MissionStatus.COMPUTING
        def done() -> None:
            self.done_compute(target=target)

        _remaining_workload = self.calc_layer_workload(target)
        _new_process = Process(
            id=self.id, 
            name=f"Computing_{self.id}", 
            arrival_time=0, 
            terminal_time=None, 
            deadline=None, 
            required_vol=_remaining_workload,
            processed_vol=processed_vol,
            callback=done,
            )
        return _new_process
    
    def done_compute(self, target: int) -> None:
        self.inference_layer = target
        self.status = MissionStatus.IDLE
        if self.inference_layer >= self.MAXIMUM_INFERENCE_LAYER:
            self.status = MissionStatus.COMPLETED

    def _produce(self, clock_frequency_ghz: float, dt_s: float):
        # GHz 转换为 Hz，再乘以时间得到总的计算量
        produced_workload = clock_frequency_ghz * 1e9 * dt_s  
        return produced_workload

    def calc_image_data_size_mb(self):
        # 计算并将结果转换为MB
        sz = (self.IMAGE_WIDTH_PX * self.IMAGE_HEIGHT_PX * self.CHANNEL_PER_PIXEL * self.BITS_PER_CHANNEL) / (1024 * 1024 * 8)
        return sz
    
    def calc_intermediate_feature_data_size_mb(self, layer_num: int):
        # 假设每层特征图的尺寸为输入图像尺寸的1/2，且每个像素的特征值占4字节（float32）
        feature_width = self.IMAGE_WIDTH_PX / (2 ** layer_num)
        feature_height = self.IMAGE_HEIGHT_PX / (2 ** layer_num)
        data_size_mb = (feature_width * feature_height * 256 * 4) / (1024 * 1024)  # 256是每层的特征图数量
        return data_size_mb
    
    def calc_layer_workload(self, layer_num: int):
        # 假设每层的计算量与特征图的像素数量成正比，且每个像素的计算量为1000次浮点运算
        feature_width = self.IMAGE_WIDTH_PX / (2 ** layer_num)
        feature_height = self.IMAGE_HEIGHT_PX / (2 ** layer_num)
        workload = feature_width * feature_height * 256 * 1000  # 256是每层的特征图数量
        return workload
    
    def calc_total_workload(self):
        total_workload = 0
        for layer in range(self.MAXIMUM_INFERENCE_LAYER):
            total_workload += self.calc_layer_workload(layer)
        return total_workload

    def snapshot(self) -> MissionSnapshot:
        if isinstance(self.start_time, Time):
            start_time = skyfield_to_datetime(self.start_time).isoformat()
        else:
            start_time = str(self.start_time)

        if isinstance(self.end_time, Time):
            end_time = skyfield_to_datetime(self.end_time).isoformat()
        else:
            end_time = str(self.end_time)

        return MissionSnapshot(
            id=self.id,
            status=self.status.value,
            position=self.position.address,
            inference_layer=self.inference_layer,
            data_size=self.data_size,
            workload=self.workload,
            start_time=start_time,
            end_time=end_time,
            deadline=str(self.deadline),
        )

    def serialize(self) -> dict:
        return self.snapshot().model_dump()