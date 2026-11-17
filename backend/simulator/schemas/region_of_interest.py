from pydantic import Field
from typing import Optional
from simulator.schemas.base import ContractModel, LatLon

class ROI(ContractModel):
    id: str
    project_id: str = Field(...)
    name: str
    length: float = Field(gt=0)
    width: Optional[float] = Field(None, gt=0)
    location: LatLon
