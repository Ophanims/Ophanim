import math
from typing import Callable, Optional


class Process:
    def __init__(
        self, 
        id: int, 
        name: str, 
        arrival_time: int, 
        terminal_time: Optional[int], 
        deadline: Optional[int], 
        required_vol: float,
        processed_vol: float,
        callback: Callable[[], None],
        ):
        self.id = id
        self.name = name
        self.status = True
        self.arrival_time = arrival_time
        self.terminal_time = terminal_time
        self.deadline = deadline
        self.required_vol = required_vol
        self.remaining_vol = required_vol
        self.processed_vol = processed_vol
        self.callback = callback
        
    def proceed(self):
        if self.status:
            self.remaining_vol -= self.processed_vol

            if self.remaining_vol <= 0:
                self.remaining_vol = 0
                self.callback()
                self.status = False
                
    def time_cost(self) -> Optional[int]:
        if self.processed_vol <= 0:
            return None  # 无法完成
        remaining_time = math.ceil(self.remaining_vol / self.processed_vol)
        return remaining_time

