"""Read-only v0 record boundary. Remove after all retained v0 records are migrated."""
from datetime import datetime
import math
from entity.mission import PhysicalMissionSnapshot
from simulator.contracts import SimulationSnapshot, RunInfo
from simulator.entities.satellite_entity import SatelliteSnapshot
from simulator.entities.station_entity import StationSnapshot
from simulator.entities.sun_entity import SunSnapshot
from simulator.entities.earth_entity import EarthSnapshot
from simulator.services.network_service import LinkSnapshot
from simulator.schemas.base import XYZ, LatLon
from simulator.schemas.project import Project


def _position(entity: dict) -> XYZ:
    return XYZ(**{axis: entity.get(axis, 0) for axis in "xyz"})


def _direction(entity: dict, prefix: str) -> XYZ:
    values = [entity.get(f"{prefix}{axis.upper()}", 0) for axis in "xyz"]
    length = math.sqrt(sum(value * value for value in values)) or 1
    return XYZ(**dict(zip("xyz", [value / length for value in values])))


def migrate_snapshot(state: dict, project: Project) -> SimulationSnapshot:
    clock = state["clock"]
    entities = state["entities"]
    addresses = {entity["addr"]: str(entity.get("id", entity["addr"])) for entity in entities}
    stations = [entity for entity in entities if entity["type"] == "ground_station"]
    for entity, station in zip(stations, project.ground_stations):
        addresses[entity["addr"]] = station.id
    positions = {entity["addr"]: _position(entity) for entity in entities}
    satellites = []
    for entity in entities:
        if entity["type"] != "earth_satellite":
            continue
        satellites.append(SatelliteSnapshot(
            id=addresses[entity["addr"]], plane=entity["plane"], order=entity["order"],
            dimensions=(0.3, 0.3, 0.3), pos=_position(entity),
            loc=LatLon(lat=entity["lat"], lon=entity["lon"]),
            velocity_vector=_direction(entity, "velocityVector"), solar_vector=_direction(entity, "solarVector"),
            img_corners_pos=[XYZ(**{axis: entity.get(f"cor{axis.upper()}{index}", 0) for axis in "xyz"}) for index in range(1, 5)],
            img_corners_loc=[LatLon(lat=entity.get(f"corLat{index}", 0), lon=entity.get(f"corLon{index}", 0)) for index in range(1, 5)],
            battery_percent=entity.get("batteryLevel", 100), cost_percent=0, gain_percent=0,
            processor_clock_frequency_ghz=entity.get("processorClockFrequency"),
            **{canonical: bool(entity.get(legacy, False)) for canonical, legacy in {
                "is_observing": "onROI", "is_processing": "onCOM", "is_charging": "onSUN",
                "is_communicating_sgl": "onSGL", "is_communicating_isl": "onISL"}.items()},
        ))
    links = [LinkSnapshot(type=link["type"], src=addresses[link["src"]], dst=addresses[link["dst"]],
                         distance=link["distance"], snr=link["snr"], rate=link["capacity"],
                         link_pos=[positions[link["src"]], positions[link["dst"]]]) for link in state["links"]]
    missions = [PhysicalMissionSnapshot.model_validate({**mission, "position": addresses.get(mission["position"], mission["position"])}) for mission in state["missions"]]
    sun = next((entity for entity in entities if entity["type"] == "the_sun"), {})
    time = clock["current_datetime"]
    elapsed = (datetime.fromisoformat(time) - datetime.fromisoformat(project.experiment.start_time)).total_seconds()
    return SimulationSnapshot(time=time, frame_counter=clock["slot_count"], period_counter=clock["slot_count"],
        slot_counter=0, max_slot_number=1, max_period_numbers=clock["maximum_slot"] + 1,
        satellites=tuple(satellites), stations=tuple(StationSnapshot(id=addresses[entity["addr"]],
            pos=_position(entity), loc=LatLon(lat=entity["lat"], lon=entity["lon"]),
            on_upload=bool(entity.get("onUpload")), on_download=bool(entity.get("onDownload"))) for entity in stations),
        rois=(), links=tuple(links), missions=tuple(missions), sun=SunSnapshot(id="sun", pos=_position(sun)),
        earth=EarthSnapshot(id="earth", pos=XYZ(x=0, y=0, z=0), rotation=elapsed * 2 * math.pi / 86400),
        info=RunInfo(num_nodes=len(satellites) + len(stations), num_edges=len(links), num_tasks=len(missions)))
