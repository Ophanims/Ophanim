from pydantic import Field
from simulator.schemas.base import ContractModel, LatLon

class GroundStation(ContractModel):
    id: str
    project_id: str = Field(...)
    altitude_m: float = 0
    name: str
    location: LatLon
