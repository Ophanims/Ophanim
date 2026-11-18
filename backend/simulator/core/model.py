"""Runtime model contract: apply a command on a staged state, then take a snapshot.

The kernel owns staging/commit. A transition never publishes or records data.
Geometry and scheduling models share this lifecycle without sharing state fields.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Generic, TypeVar


State = TypeVar("State")
Action = TypeVar("Action")


@dataclass(frozen=True)
class StepContext:
    time: datetime
    dt_s: float
    frame_counter: int

    def __post_init__(self):
        if not isfinite(self.dt_s) or self.dt_s <= 0:
            raise ValueError("dt_s must be finite and positive")


class SimulationModel(ABC, Generic[State, Action]):
    @abstractmethod
    def snapshot(self) -> State:
        """Return a detached view of the current state."""

    @abstractmethod
    def transition(self, action: Action, context: StepContext) -> State:
        """Compute f(s_t, a_t, dt) on the kernel's private candidate state."""


@dataclass(frozen=True)
class GeometryAction:
    period_counter: float
    slot_counter: int = 0


class SampledModel(SimulationModel):
    """Geometry-only transition, specialized by resource-bearing subclasses."""

    def transition(self, action: GeometryAction, context: StepContext):
        self.tick(action.period_counter, action.slot_counter)
        return self.snapshot()
