import itertools
from typing import Optional

from pydantic import BaseModel

from status.mission_status import MissionStatus
from controller.project_controller import ProjectBase

class MissionSnapshot(BaseModel):
    id: str
    status: str
    position: dict
    inference_layer: str
    data_size: float
    workload: float
    start_time: str
    end_time: str
    deadline: str

class Mission():
    _id_counter = itertools.count(1)
    def __init__(self, position: dict, start_time: str):
        self.id = self._next_unique_id(type)
        self.status = MissionStatus.PENDING
        self.phase = MissionStatus.UPLOADING
        
        self.IMAGE_WIDTH_PX = 10000
        self.IMAGE_HEIGHT_PX = 10000
        self.BITS_PER_CHANNEL = 8
        self.CHANNEL_PER_PIXEL = 3
        self.MAXIMUM_INFERENCE_LAYER = 7
        
        self.position = position
        self.inference_layer = 0
        self.data_size = self.INITIAL_DATA_SIZE_MB
        self.workload = 0
        self.start_time = start_time
        self.end_time = ""
        self.deadline = ""
        
    @classmethod
    def _next_unique_id(cls) -> str:
        # 使用统一递增计数，确保当前进程内全局唯一。
        return f"M{next(cls._id_counter):08d}"
        
    def setup(self, project: ProjectBase):
        self.IMAGE_WIDTH_PX = project.imageryWidthPx or 0
        self.IMAGE_HEIGHT_PX = project.imageryHeightPx or 0
        self.BITS_PER_CHANNEL = project.bitsPerChannelBit or 0
        self.CHANNEL_PER_PIXEL = project.channelsPerPixel or 0
        
        self.data_size = self.calc_image_data_size_mb()
        
    def tick(self):
        pass
        
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

    def snapshot(self) -> MissionSnapshot:
        return MissionSnapshot(
            id=self.id,
            position=self.position,
            inference_layer=self.inference_layer,
            data_size=self.data_size,
            workload=self.workload,
            start_time=self.start_time,
            end_time=self.end_time,
            deadline=self.deadline
        )

    def serialize(self) -> dict:
        return self.snapshot().model_dump()