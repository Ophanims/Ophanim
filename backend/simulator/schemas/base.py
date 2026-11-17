from pydantic import BaseModel, ConfigDict, Field
from typing import TypeVar, Generic, Self

T = TypeVar("T")

class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    def snapshot(self) -> Self:
        return self.model_copy(deep=True)

    def serialize(self) -> dict:
        return self.snapshot().model_dump(mode="json")


class SnapshotModel(ContractModel):
    model_config = ConfigDict(frozen=True, json_schema_serialization_defaults_required=True)


class XYZ(SnapshotModel):
    x: float
    y: float
    z: float


class LatLon(SnapshotModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class ApiResponse(BaseModel, Generic[T]):
    status: str
    data: T
