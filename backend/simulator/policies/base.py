"""A scheduler owns policy memory and only borrows a detached planning view."""
from typing import Protocol
from simulator.contracts import SimulationSnapshot
from simulator.core.actions import SchedulingActions
from simulator.core.model import StepContext


class DecisionPolicy(Protocol):
    def decide(self, state: SimulationSnapshot, context: StepContext) -> SchedulingActions:
        """Return the complete slot's ID-only actions."""


class SchedulingPolicy:
    def initialize(self, view):
        """Initialize strategy-specific memory, when needed."""

    def __getattr__(self, name):
        view = self.__dict__.get("_view")
        if view is not None:
            return getattr(view, name)
        raise AttributeError(name)

    def decide(self, view, context: StepContext) -> SchedulingActions:
        self.initialize(view)
        self._view = view
        try:
            return self.decide_actions()
        finally:
            del self._view
