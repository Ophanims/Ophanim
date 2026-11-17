from typing import Optional
from pydantic import Field
from simulator.schemas.base import ContractModel


class SatelliteConfig(ContractModel):
    id: str
    constellation_id: Optional[str] = Field(None)
    name: Optional[str] = None
    order: Optional[int] = None
    plane: Optional[int] = None
    tle1: Optional[str] = None
    tle2: Optional[str] = None
