from enum import Enum
    
class MissionStatus(Enum):
    # Idle（空闲）
    IDLE = "idle"
    # Transmitting（进行传输）
    TRANSMITTING = "transmitting"
    # Processing（进行执行）
    PROCESSING = "processing"
    # Completed（完成）
    COMPLETED = "completed"
    # Failed（失败）
    FAILED = "failed"
    
class MissionPhase(Enum):
    # Uploading（上传中）：包括等待上传和正在上传
    UPLOADING = "uploading"
    # Sensing（感知中）：包括卫星以感知为目的进行的成像和卫星间为了获取成像机会的调度
    SENSING = "sensing"
    # Computing（计算中）：包括卫星上的边缘计算和卫星间为了分工计算进行的调度
    COMPUTING = "computing"
    # Downloading（下载中）：包括等待下载和正在下载进行的调度
    DOWNLOADING = "downloading"