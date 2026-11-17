from pydantic import Field
from typing import Optional
from simulator.schemas.base import ContractModel

class Constellation(ContractModel):
    id: str
    project_id: str = Field(...)
    name: str
    description: Optional[str] = None
    number_of_planes: int = Field(..., ge=1, le=100)
    number_of_sat_per_planes: int = Field(..., ge=1, le=100)
    phase_factor: float = Field(...)
    altitude: float = Field(..., gt=0)
    inclination: float = Field(..., ge=0, le=180)
    orbital_period: Optional[float] = Field(None)
