"""Canonical metadata, playback and analysis contracts for a simulation record."""
from typing import Literal
from pydantic import Field
from simulator.contracts import SimulationSnapshot
from simulator.entities.satellite_entity import SatelliteSnapshot
from simulator.entities.station_entity import StationSnapshot
from simulator.schemas.base import SnapshotModel
from simulator.schemas.project import Project
from simulator.schemas.task import Task
from simulator.services.network_service import LinkSnapshot
from entity.mission import PhysicalMissionSnapshot


class RecordSnapshot(SnapshotModel):
    schema_version: Literal[1] = 1
    record_id: str = Field(pattern=r"^(?:[0-9a-f]{32}|timescale_[1-9][0-9]*)$")
    project_id: str
    project: Project
    code_hash: str
    algorithm: str
    status: str
    frame_count: int = 0


class RecordWindow(SnapshotModel):
    record: RecordSnapshot
    frames: tuple[SimulationSnapshot, ...]
    start_frame: int
    has_more: bool


class NetworkMetrics(SnapshotModel):
    num_nodes: int
    num_edges: int
    num_tasks: int
    reward: float
    average_battery_percent: float


EntityType = Literal["satellites", "stations", "tasks", "missions", "links", "network"]


class AnalysisPoint(SnapshotModel):
    time: str
    frame_counter: int
    entity_type: EntityType
    payload: SatelliteSnapshot | StationSnapshot | Task | PhysicalMissionSnapshot | LinkSnapshot | NetworkMetrics


class AnalysisWindow(SnapshotModel):
    record_id: str
    points: tuple[AnalysisPoint, ...]
    has_more: bool
    start_point: int
    next_start_point: int | None
