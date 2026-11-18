"""One simulator per session; only its decision policy varies."""
from simulator.contracts import RunInfo, SimulationSnapshot
from simulator.core.simulation import Simulation
from simulator.core.kernel import DecisionPolicy, SimulationKernel
from simulator.policies.registry import create_policy
from simulator.schemas.project import Project


class SimulationSession:
    def __init__(self, project: Project, algorithm: str = "geometry", policy: DecisionPolicy | None = None):
        self.algorithm = algorithm
        self.custom_policy = policy is not None
        self.policy = policy if self.custom_policy else create_policy(algorithm, project)
        self.environment = Simulation(project)
        self.kernel = SimulationKernel()
        self.info = self.environment.info
        self.is_completed = False
        self._state = self.environment.snapshot()

    def step(self) -> SimulationSnapshot:
        if self.is_completed:
            return self.snapshot()
        return self.kernel.advance(self)

    def snapshot(self) -> SimulationSnapshot:
        return self._state.model_copy(deep=True)

    def collect_snapshot(self, environment, info) -> SimulationSnapshot:
        return environment.snapshot().model_copy(update={"info": RunInfo.model_validate(info)})

    def close(self) -> None:
        self.environment.close()
