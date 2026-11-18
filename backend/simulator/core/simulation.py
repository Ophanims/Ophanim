"""The only simulation environment, independent of the selected policy."""
from datetime import timedelta
from simulator.contracts import RunInfo, SimulationSnapshot
from simulator.core.actions import SchedulingActions
from simulator.core.model import SimulationModel, StepContext
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.core.staging import fork_environment
from simulator.core.time_step import step_context
from simulator.env.core.entity_col import EntityCol
from simulator.env.core.logger import SystemLogger
from simulator.env.core.task_manager import TaskManager
from simulator.schemas.project import Project


class Simulation(SimulationModel):
    def __init__(self, project: Project):
        self.input = project.snapshot()
        self.logger = SystemLogger("Simulation")
        self.reset()

    def reset(self, seed=None):
        self.__dict__.update(load_input_metadata(self.input, timedelta(hours=2)))
        self.period_in_num = self.period.total_seconds()
        self.slot = self.period
        self.slot_in_num = self.period_in_num
        self.max_slot_number = 1
        self.slot_counter = self.period_counter = self.frame_counter = 0
        objects = build_static_objects(self.input, self.period, self.max_period_numbers, self.datetime_list)
        self.sat, self.gs, self.roi = objects["sat"], objects["gs"], objects["roi"]
        self.eth, self.sun = objects["eth"], objects["sun"]
        self.net = init_network(self.input, objects["sat_datas"], objects["gs_datas"])
        for entity in [*self.sat, *self.gs, *self.roi, self.eth, self.sun]:
            entity.tick(0, 0)
        self.net._at(0, 0)
        self.entity_collection = EntityCol(self.input)
        self.entity_collection.reset(self.sat, self.net.compute_isl_links_at(0, 0))
        self.task_manager = TaskManager(self.entity_collection)
        self.task_manager.reset(slot=self.slot_in_num, seed=seed)
        self.comp_reqs, self.trans_reqs = [], []
        self.task_isl_hops = {}
        self.at_ground = self.at_sunlit_sat = self.at_dark_sat = 0
        self.info = RunInfo()
        self.is_completed = False
        self.match_tasks()
        return self.snapshot()

    def match_tasks(self):
        for node in self.sat:
            node.matching_task_queue([task for task in self.task_manager.get_tasks_at(self.frame_counter)
                if (task.plane_at, task.order_at) == (node.plane, node.order)])

    def transition(self, actions: SchedulingActions, context: StepContext) -> SimulationSnapshot:
        """Apply the one physics implementation to a private candidate world."""
        from simulator.core.world_transition import execute_actions
        execute_actions(self, actions, context)
        self.match_tasks()
        ended = self.time_recorder >= self.t_end
        completed = bool(self.task_manager.tasks) and all(task.is_done for task in self.task_manager.tasks)
        depleted = any(node.battery_ratio <= 0 for node in self.sat)
        self.is_completed = ended or completed or depleted
        self.info = RunInfo(num_nodes=len(self.sat), num_edges=len(self.net._all_links),
            num_tasks=len(self.task_manager.get_tasks_at(self.frame_counter)),
            is_terminated=self.is_completed,
            terminated_reason="all_tasks_completed" if completed else "satellite_energy_depleted" if depleted
                              else "end_time_reached" if ended else "None")
        return self.snapshot()

    def step(self, actions: SchedulingActions = SchedulingActions()):
        if self.is_completed:
            return self.snapshot()
        candidate = fork_environment(self)
        state = candidate.transition(actions, step_context(candidate))
        state.model_dump_json()
        self.__dict__ = candidate.__dict__
        return state

    def snapshot(self) -> SimulationSnapshot:
        return SimulationSnapshot(time=self.time_recorder.isoformat(), frame_counter=self.frame_counter,
            slot_counter=self.slot_counter, max_slot_number=self.max_slot_number,
            period_counter=self.period_counter, max_period_numbers=self.max_period_numbers,
            satellites=tuple(entity.snapshot() for entity in self.sat),
            stations=tuple(entity.snapshot() for entity in self.gs), rois=tuple(entity.snapshot() for entity in self.roi),
            links=tuple(self.net._all_links), sun=self.sun.snapshot(), earth=self.eth.snapshot(),
            tasks=tuple(task.snapshot() for task in self.task_manager.tasks), info=self.info).model_copy(deep=True)

    def close(self):
        self.logger.close()
