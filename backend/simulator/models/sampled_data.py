"""Bounded, on-demand samples behind the environments' existing indexing interface."""
from collections import OrderedDict
from collections.abc import Sequence

import numpy as np


class SampleSeries(Sequence):
    def __init__(self, timeline, sample, sample_many=None):
        self.timeline = timeline
        self.sample = sample
        self.sample_many = sample_many

    def __len__(self) -> int:
        return len(self.timeline)

    def __getitem__(self, index):
        if isinstance(index, slice):
            indices = range(*index.indices(len(self)))
            if self.sample_many is not None:
                return self.sample_many(indices)
            return np.asarray([self.sample(position) for position in indices])
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return self.sample(index)


class SampleCache:
    """Own a small cache per calculator; never retain a full trajectory."""
    def __init__(self, capacity: int = 4):
        self.capacity = capacity
        self.samples = OrderedDict()

    def get(self, index, calculate):
        if index not in self.samples:
            self.samples[index] = calculate(index)
            if len(self.samples) > self.capacity:
                self.samples.popitem(last=False)
        else:
            self.samples.move_to_end(index)
        return self.samples[index]


def sample_columns(timeline, calculator, fields):
    return {field: SampleSeries(timeline, lambda index, field=field: calculator.at(index)[field])
            for field in fields}
