from pydantic import BaseModel, ConfigDict
from simulator.core.model import SimulationModel, StepContext
from simulator.core.actions import TaskAction
from simulator.config import LAYER_PROCESS_SECOND_COST_GPU, MAX_NUM_LAYERS

"""
Each task record Z = {m, n, p, o, start, end}
- m: task index
- n: layer index
- p: plane index
- o: satellite index
- start: int
- end: int
"""

class TaskState(BaseModel):
    model_config = ConfigDict(json_schema_serialization_defaults_required=True, allow_inf_nan=False)
    id: int
    plane_at: int
    order_at: int
    t_start: int
    t_end: int

    # functional counters
    layer_id: int = 0
    completion: float = 0.0
    acted: int = 0 # to record action taken
    workload_done: float = 0 # computation progress in nominal slots
    workload_percent: float = 0.0
    data_sent : float = 0.0 # to record transmission progress
    data_percent: float = 0.0
    is_done: bool = False

    # ddl temp.
    ddl: int = 0


class TaskSnapshot(TaskState):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False,
                             json_schema_serialization_defaults_required=True)


class Task(TaskState, SimulationModel):
    def snapshot(self) -> "TaskSnapshot":
        return TaskSnapshot.model_validate(self.model_dump())

    def transition(self, action: TaskAction, context: StepContext) -> "TaskSnapshot":
        if action.kind == "age":
            self.t_end += action.elapsed_slots
        elif not self.is_done:
            if action.acted is not None:
                self.acted = action.acted
            if action.kind == "compute":
                duration = LAYER_PROCESS_SECOND_COST_GPU[self.layer_id]
                self.workload_done += context.dt_s / action.nominal_slot_s
                self.workload_percent = self.workload_done * action.nominal_slot_s / duration
                if self.workload_percent >= 1 - 1e-12:
                    self.layer_id += 1
                    self.workload_done = 0
                    self.workload_percent = 0.0
                    self.completion = (sum(LAYER_PROCESS_SECOND_COST_GPU[:self.layer_id]) /
                                       sum(LAYER_PROCESS_SECOND_COST_GPU) if action.weighted_completion
                                       else self.layer_id / MAX_NUM_LAYERS)
                    self.is_done = self.layer_id >= MAX_NUM_LAYERS
            elif action.kind == "transfer":
                if action.data_bits < 0 or action.target_bits <= 0:
                    raise ValueError("Transfer requires nonnegative data and positive target_bits")
                self.data_sent += action.data_bits
                self.data_percent = self.data_sent / action.target_bits
                if self.data_percent >= 1:
                    self.data_sent = self.data_percent = 0.0
                    if action.to_ground:
                        self.completion, self.is_done = 1.0, True
                    elif action.dst_plane is not None and action.dst_order is not None:
                        self.plane_at, self.order_at = action.dst_plane, action.dst_order
        return self.snapshot()
