from pydantic import Field
from typing import List, Optional
from simulator.schemas.base import ContractModel
from simulator.schemas.mission import Mission

class Experiment(ContractModel):
    id: str
    project_id: str = Field(...)
    start_time: str = Field(...)
    end_time: Optional[str] = Field(None)
    time_slot: Optional[float] = Field(None, gt=0)
    missions: List[Mission]
