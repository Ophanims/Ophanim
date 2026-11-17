"""Session-owned geometry simulation with explicit endpoint semantics."""
from datetime import timedelta
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.schemas.project import Project


class Simulation:
    def setup(self, input: Project) -> None:
        metadata = load_input_metadata(input, timedelta(hours=2))
        self.__dict__.update(metadata)
        self.input = input.snapshot()
        self.slot = self.period
        self.slot_in_num = self.period.total_seconds()
        self.max_slot_number = 1
        self.slot_counter = 0
        self.period_counter = 0
        self.frame_counter = 0
        objects = build_static_objects(input, self.period, self.max_period_numbers, self.datetime_list)
        self.sat, self.gs, self.roi = objects["sat"], objects["gs"], objects["roi"]
        self.eth, self.sun = objects["eth"], objects["sun"]
        self.net = init_network(input, objects["sat_datas"], objects["gs_datas"])
        self.period_update()

    def period_update(self) -> None:
        for entity in [*self.sat, *self.gs, *self.roi, self.eth, self.sun]:
            entity.tick(self.period_counter, self.slot_counter)
        self.net._at(self.period_counter, self.slot_counter)
        for satellite in self.sat:
            satellite.connections = {link.dst: link for link in self.net._all_links if link.src == satellite.id}

    def step(self) -> tuple[bool, dict]:
        if self.time_recorder >= self.t_end:
            return True, {}
        self.period_counter += 1
        self.frame_counter += 1
        self.time_recorder = min(self.datetime_list[self.period_counter], self.t_end)
        self.period_update()
        return self.time_recorder >= self.t_end, {}
