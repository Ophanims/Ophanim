from typing import Optional


class Process:
    def __init__(self, id: int, name: str, arrival_time: int, terminal_time: Optional[int], deadline: Optional[int], required_vol: float):
        self.id = id
        self.name = name
        self.arrival_time = arrival_time
        self.terminal_time = terminal_time
        self.deadline = deadline
        self.required_vol = required_vol
        self.remaining_vol = required_vol

    def is_finished(self) -> bool:
        return self.remaining_vol <= 0

    def process(self, processed_vol: float):
        self.remaining_vol -= processed_vol

        if self.remaining_vol <= 0:
            self.remaining_vol = 0
