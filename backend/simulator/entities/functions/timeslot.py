import datetime
from typing import Any

import numpy as np


def date_to_timeslot(t: datetime, times: Any) -> int:

    time64 = np.datetime64(t)
    index = np.searchsorted(times, time64)
    if index >= len(times):
            raise ValueError(f"时间 {t} 超出数据范围")
    return index
