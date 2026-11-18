"""A link owns the finite transmission budget for one interval."""
from dataclasses import dataclass
from math import isfinite
from simulator.core.model import SimulationModel, StepContext
from simulator.services.network_service import LinkSnapshot


@dataclass(frozen=True)
class LinkAction:
    # Positive relative weights, collected before any task makes progress.
    users: tuple[tuple[int, float], ...]


class LinkEntity(SimulationModel):
    def __init__(self, state: LinkSnapshot):
        self.state = state.model_copy(deep=True)
        self.allocated_bits: dict[int, float] = {}

    def snapshot(self) -> LinkSnapshot:
        return self.state.model_copy(deep=True)

    def transition(self, action: LinkAction, context: StepContext) -> LinkSnapshot:
        users = dict(action.users)
        if len(users) != len(action.users) or any(not isfinite(w) or w <= 0 for w in users.values()):
            raise ValueError("Link users must be distinct with finite positive weights")
        total = sum(users.values())
        budget = max(0.0, self.state.rate) * context.dt_s
        self.allocated_bits = {task_id: budget * weight / total for task_id, weight in users.items()}
        return self.snapshot()
