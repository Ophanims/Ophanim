

from typing import List, Optional, Literal
from pydantic import Field

from simulator.schemas.base import ContractModel
from simulator.schemas.resources import Resources
from simulator.schemas.constellation import Constellation
from simulator.schemas.experiment import Experiment
from simulator.schemas.ground_station import GroundStation
from simulator.schemas.hardware import Hardware
from simulator.schemas.region_of_interest import ROI
from simulator.schemas.satellite import SatelliteConfig


class Project(ContractModel):
    schema_version: Literal[1] = 1
    algorithm: Literal["ophanim", "geometry", "l2d2", "phoenix", "mhspo", "ppo"] = "geometry"
    resources: Resources = Field(default_factory=Resources)
    seed: int = 0
    project_id: str
    user_id: Optional[str] = Field(None)
    title: str
    description: str
    hardware: Hardware
    experiment: Experiment
    constellation: Constellation
    satellites: List[SatelliteConfig]
    ground_stations: List[GroundStation] = Field(...)
    rois: List[ROI]
