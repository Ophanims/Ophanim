
from typing import Optional
from pydantic import Field
from simulator.schemas.base import ContractModel


class Mission(ContractModel):
    id: str
    project_id: str = Field(...)
    name: str
    target_id: str = Field(...)
    source_node_id: str = Field(...)
    end_node_id: str = Field(...)
    start_time: str = Field(...)
    end_time: Optional[str] = Field(None)
    duration: Optional[float] = None  # in seconds
