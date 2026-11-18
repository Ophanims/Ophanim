"""Read models translating common tasks/nodes into the original planner's units.

These are observations only. They own no clock, task lifecycle or physics loop.
"""
import math
from types import SimpleNamespace
from skyfield.api import EarthSatellite
from simulator.config import BATTERY_MAX, COMPUTE_ENERGY_COST, LAYER_OUTPUT_DATA_SIZE, LAYER_PROCESS_SECOND_COST_GPU
from simulator.models.realtime_ephemeris import TS
from status.mission_status import MissionPhase, MissionStatus


class SatelliteObservation:
    def __init__(self, node, config, project, slot_s):
        self.addr = self.id = node.id
        self.plane, self.order = node.plane, node.order
        self.type = "earth_satellite"
        self.battery_percent = node.battery_ratio * 100
        self.BATTERY_CAPACITY = BATTERY_MAX / 3600
        resources = project.resources
        self.processor_clock_frequency_ghz = max(resources.max_clock_frequency_ghz, 1e-9)
        self.power_of_solar_panel = resources.solar_panel_area_m2 * resources.solar_panel_efficiency * 1361
        self.power_of_computing = abs(COMPUTE_ENERGY_COST)
        self.connections = []
        self.motion = EarthSatellite(config.tle1, config.tle2, node.id, TS)
        self.slot_s = slot_s

    def at(self, time):
        return self.motion.at(time)

    def is_sunlit(self, time):
        from simulator.config import EPHEMERIS
        return self.at(time).is_sunlit(EPHEMERIS)

    def get_orbital_cycle(self):
        seconds = 2 * math.pi / self.motion.model.no_kozai * 60
        return seconds, math.ceil(seconds / self.slot_s)


class TaskObservation:
    def __init__(self, task, node, origin, frame_counter, busy):
        self.task = task
        self.id, self.position, self.src = task.id, node, origin
        self.status = MissionStatus.COMPLETED if task.is_done else MissionStatus.PROCESSING if busy else MissionStatus.IDLE
        self.phase = MissionPhase.COMPUTING if busy else MissionPhase.UPLOADING
        # Each unreserved inference layer is a newly schedulable job. The
        # canonical task's original arrival/deadline remain untouched.
        self.start_slot = max(task.t_start, frame_counter)
        self.deadline_slot = task.ddl
        self.data_size = LAYER_OUTPUT_DATA_SIZE[min(task.layer_id, len(LAYER_OUTPUT_DATA_SIZE) - 1)]

    def calc_total_workload(self):
        duration_s = sum(LAYER_PROCESS_SECOND_COST_GPU[self.task.layer_id:])
        return duration_s * self.position.processor_clock_frequency_ghz * 1e9


def observe_world(view, origins):
    configs = {satellite.id: satellite for satellite in view.input.satellites}
    satellites = [SatelliteObservation(node, configs[node.id], view.input, view.slot_in_num) for node in view.sat]
    nodes = {node.addr: node for node in satellites}
    nodes.update({station.id: SimpleNamespace(addr=station.id, type="ground_station") for station in view.gs})
    for link in view.net._all_links:
        if link.type == "DL" and link.src in nodes:
            nodes[link.src].connections.append(SimpleNamespace(status=True, dst=nodes[link.dst],
                capacity=link.rate * view.slot_in_num, processes=[]))
    locations = {(node.plane, node.order): node for node in satellites}
    busy = {request["task_id"] for request in [*view.comp_reqs, *view.trans_reqs]}
    missions = []
    for task in view.task_manager.tasks:
        node = locations[(task.plane_at, task.order_at)]
        origins.setdefault(task.id, node.id)
        missions.append(TaskObservation(task, node, nodes[origins[task.id]], view.frame_counter, task.id in busy))
    from core.prediction_cache import PredictionCache
    return SimpleNamespace(satellites=satellites, missions=missions, prediction_cache=PredictionCache())
