"""The original Ophanim physics/mission model as a strategy of the one application."""
import math
from datetime import timedelta
import numpy as np
from core.session_context import physics_context, new_identity_sequences
from core.simulation_clock import SimulatorClock
from core.simulation_world import SimulationWorld
from entity.sat import Satellite
from simulator.schemas.engine_config import EngineConfig, EngineStation
from simulator.schemas.project import Project
from simulator.core.initialisation import load_input_metadata
from simulator.entities.functions.prepare import preparation_of_roi, to_times
from simulator.contracts import SimulationSnapshot, RunInfo
from simulator.entities.satellite_entity import SatelliteSnapshot
from simulator.entities.station_entity import StationSnapshot
from simulator.entities.earth_entity import EarthSnapshot
from simulator.entities.sun_entity import SunSnapshot
from simulator.services.network_service import LinkSnapshot
from simulator.schemas.base import XYZ, LatLon
from util.time_utils import to_skyfield_time


class PhysicsEnvironment:
    def __init__(self, project: Project):
        self.project = project.snapshot()
        self.clock = SimulatorClock()
        self.identity = new_identity_sequences()
        with physics_context(self.clock, None, self.identity):
            self.world = SimulationWorld()
        self.frame_counter = self.period_counter = self.slot_counter = 0
        self.max_slot_number = 1
        self.slot_in_num = project.experiment.time_slot or 30
        self.t_end = None

    def reset(self):
        metadata = load_input_metadata(self.project, 7200)
        configuration = EngineConfig.from_project(self.project)
        configuration.start_time = metadata["t_start"].isoformat()
        configuration.end_time = metadata["t_end"].isoformat()
        with physics_context(self.clock, self.world, self.identity):
            self.clock.setup(configuration)
            self.clock.END_SLOT = math.ceil((self.clock.END_DATETIME - self.clock.START_DATETIME).total_seconds() / self.clock.SLOT)
            satellites = []
            for index, config in enumerate(self.project.satellites):
                satellite = Satellite(config.tle1, config.tle2, index, config.plane, config.order)
                satellite.id = config.id
                satellites.append(satellite)
            stations = [EngineStation(name=station.name, latitude=station.location.lat,
                                      longitude=station.location.lon, altitude=station.altitude_m)
                        for station in self.project.ground_stations]
            self.world.setup(configuration, stations, satellites=satellites)
            for entity in self.world.entities:
                entity.move() if isinstance(entity, Satellite) else entity.tick()
            self._refresh_links()
        self.time_recorder = self.clock.current_datetime
        self.t_end = self.clock.END_DATETIME
        self.max_period_numbers = self.clock.END_SLOT + 1
        self.roi, _ = preparation_of_roi(self.project, metadata["max_period_numbers"],
                                         to_times(metadata["datetime_list"]), metadata["datetime_list"])
        for roi in self.roi:
            roi.tick(0, 0)
        return None

    def _refresh_links(self):
        for node in self.world.nodes:
            node.connections.clear()
        for link in self.world.links:
            link.refresh()
            if link.status:
                link.src.connections.append(link)

    def step(self):
        with physics_context(self.clock, self.world, self.identity):
            remaining_s = (self.t_end - self.clock.current_datetime).total_seconds()
            if remaining_s <= 0:
                return 0.0, True, False, {}
            configured_slot = self.clock.SLOT
            self.clock.SLOT = min(configured_slot, remaining_s)
            try:
                self.clock.tick()
                self.world.tick()
            finally:
                self.clock.SLOT = configured_slot
            self.time_recorder = self.clock.current_datetime
            self.frame_counter = self.period_counter = self.clock.current_slot
            for roi in self.roi:
                roi.tick(min(self.period_counter, self.max_period_numbers - 1), 0)
            completed = self.time_recorder >= self.t_end
            return 0.0, completed, False, {"num_nodes": len(self.world.nodes),
                "num_edges": sum(link.status for link in self.world.links),
                "num_tasks": len(self.world.missions), "is_terminated": completed,
                "terminated_reason": "end_time_reached" if completed else "None"}

    @staticmethod
    def _direction(x, y, z) -> XYZ:
        length = math.sqrt(x*x + y*y + z*z)
        return XYZ(x=x/length, y=y/length, z=z/length) if length else XYZ(x=0, y=0, z=0)

    def snapshot(self) -> SimulationSnapshot:
        with physics_context(self.clock, self.world, self.identity):
            return self._collect_snapshot()

    def _collect_snapshot(self) -> SimulationSnapshot:
        identifiers = {entity.addr: entity.id for entity in self.world.satellites}
        identifiers.update({station.addr: config.id for station, config in zip(self.world.ground_stations, self.project.ground_stations)})
        satellites = []
        for satellite in self.world.satellites:
            state = satellite.snapshot()
            satellites.append(SatelliteSnapshot(
                id=satellite.id, plane=state.plane, order=state.order, dimensions=(0.3, 0.3, 0.3),
                pos=XYZ(x=state.x, y=state.y, z=state.z), loc=LatLon(lat=state.lat, lon=state.lon),
                velocity_vector=self._direction(state.velocity_vector_x, state.velocity_vector_y, state.velocity_vector_z),
                solar_vector=self._direction(state.solar_vector_x, state.solar_vector_y, state.solar_vector_z),
                img_corners_pos=[XYZ(x=getattr(state, f"cor_x{i}"), y=getattr(state, f"cor_y{i}"), z=getattr(state, f"cor_z{i}")) for i in range(1,5)],
                img_corners_loc=[LatLon(lat=getattr(state, f"cor_lat{i}"), lon=getattr(state, f"cor_lon{i}")) for i in range(1,5)],
                battery_percent=state.battery_percent, cost_percent=0, gain_percent=0,
                processor_clock_frequency_ghz=state.processor_clock_frequency_ghz,
                is_observing=bool(state.is_observing), is_processing=bool(state.is_processing),
                is_communicating_isl=bool(state.is_communicating_isl), is_communicating_sgl=bool(state.is_communicating_sgl),
                is_charging=bool(state.is_charging), task_queue=len(satellite.missions),
            ))
        stations = [StationSnapshot(id=identifiers[station.addr], pos=XYZ(x=station.x,y=station.y,z=station.z),
                    loc=LatLon(lat=station.lat,lon=station.lon),on_upload=station.on_upload,on_download=station.on_download)
                    for station in self.world.ground_stations]
        links = [LinkSnapshot(type=link.type.value, src=identifiers[link.src.addr],dst=identifiers[link.dst.addr],
                 distance=link.distance,link_pos=[XYZ(x=link.src.x,y=link.src.y,z=link.src.z),XYZ(x=link.dst.x,y=link.dst.y,z=link.dst.z)],
                 snr=link.snr,rate=link.capacity) for link in self.world.links if link.status]
        sun = next(entity for entity in self.world.entities if entity.type == "the_sun")
        elapsed = (self.time_recorder - self.clock.START_DATETIME).total_seconds()
        missions = [mission.snapshot().model_copy(update={"position": identifiers.get(mission.position.addr, mission.position.addr)}) for mission in self.world.missions]
        return SimulationSnapshot(time=self.time_recorder.isoformat(),frame_counter=self.frame_counter,
            slot_counter=0,max_slot_number=1,period_counter=self.period_counter,max_period_numbers=self.max_period_numbers,
            satellites=tuple(satellites),stations=tuple(stations),rois=tuple(roi.snapshot() for roi in self.roi),links=tuple(links),
            sun=SunSnapshot(id=sun.addr,pos=XYZ(x=sun.x,y=sun.y,z=sun.z)),
            earth=EarthSnapshot(id="earth",pos=XYZ(x=0,y=0,z=0),rotation=elapsed*2*math.pi/86400),
            missions=tuple(missions),info=RunInfo(num_nodes=len(self.world.nodes),num_edges=len(links),num_tasks=len(missions)))

    def close(self):
        self.world.clear()
