from typing import List

from controller.project_controller import GroundStationBase
from entity.gs import GroundStation


def generate_stations(gs_models: List[GroundStationBase]) -> List[GroundStation]:
    stations: List[GroundStation] = []
    for gs_model in gs_models:
        station = GroundStation(
            name=gs_model.name,
            lon=gs_model.longitude,
            lat=gs_model.latitude,
            alt=gs_model.altitude
        )
        stations.append(station)
    return stations
    