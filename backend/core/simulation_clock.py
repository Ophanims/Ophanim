from datetime import datetime, timedelta, timezone

from skyfield.timelib import Time
from util.time_utils import parse_datetime, to_skyfield_time
from controller.project_controller import ProjectBase

class SimulatorClock:
    """模拟器时钟，负责管理当前时间和时间槽的转换"""

    def __init__(self):
        self.SLOT: int = 0
        
        self.START_SLOT: int = 0
        self.START_TIME: Time = None
        self.START_DATETIME: datetime = None
        
        self.END_SLOT: int = 0
        self.END_TIME: Time = None
        self.END_DATETIME: datetime = None
        
        self.current_datetime: datetime = None
        self.current_time: Time = None
        self.current_slot: int = 0
        
    def setup(self, project: ProjectBase):
        self.SLOT = project.timeSlot if project.timeSlot and project.timeSlot > 0 else 1
        
        T_START = parse_datetime(project.startTime) if project.startTime else None
        T_END = parse_datetime(project.endTime) if project.endTime else None
        
        if T_START is None:
            self.START_DATETIME = datetime.now(timezone.utc)
        else:
            self.START_DATETIME = T_START

        if T_END is None or T_END < self.START_DATETIME:
            self.END_DATETIME = self.START_DATETIME + timedelta(days=1)
        else:
            self.END_DATETIME = T_END
            
        self.START_TIME = to_skyfield_time(self.START_DATETIME)
        self.END_TIME = to_skyfield_time(self.END_DATETIME)
        
        self.START_SLOT = 0
        self.END_SLOT = int((self.END_DATETIME - self.START_DATETIME).total_seconds() / self.SLOT)
        
        self.current_slot = self.START_SLOT
        self.current_datetime = self.START_DATETIME
        self.current_time = self.START_TIME

    def tick(self):
        """推进一个时间槽"""
        if self.current_datetime is None:
            self.current_datetime = self.START_DATETIME
        self.current_datetime = self.current_datetime + timedelta(seconds=self.SLOT)
        self.current_time = to_skyfield_time(self.current_datetime)
        self.current_slot += 1
        
    def snapshot(self) -> dict:
        """返回当前时钟状态的快照"""
        return {
            "current_datetime": self.current_datetime.isoformat() if self.current_datetime else None,
            "slot_count": self.current_slot,
            "slot_duration": self.SLOT,
            "maximum_slot": self.END_SLOT,
            "start_time": self.START_DATETIME.isoformat() if self.START_DATETIME else None,
            "end_time": self.END_DATETIME.isoformat() if self.END_DATETIME else None,
        }
        
        
CLOCK = SimulatorClock()