"""Index simulation dates without allocating the entire experiment timeline."""
import math
from collections.abc import Sequence
from datetime import datetime, timedelta


class SimulationTimeline(Sequence):
    def __init__(self, t_start: datetime, t_end: datetime, period: timedelta):
        self.t_start = t_start
        self.t_end = t_end
        self.period = period
        self.sample_count = max(2, math.ceil((t_end - t_start) / period) + 1)

    def __len__(self) -> int:
        return self.sample_count

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[position] for position in range(*index.indices(len(self))) ]
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return min(self.t_start + index * self.period, self.t_end)
