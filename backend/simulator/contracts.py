"""Versioned runtime state and commands, shared by every transport consumer."""
from typing import Literal
from pydantic import Field
from simulator.schemas.base import ContractModel, SnapshotModel
from simulator.schemas.project import Project
from simulator.entities.satellite_entity import SatelliteSnapshot
from simulator.entities.station_entity import StationSnapshot
from simulator.entities.roi_entity import ROISnapshot
from simulator.entities.earth_entity import EarthSnapshot
from simulator.entities.sun_entity import SunSnapshot
from simulator.services.network_service import LinkSnapshot
from simulator.schemas.task import TaskSnapshot
from entity.mission import PhysicalMissionSnapshot


class RunInfo(SnapshotModel):
    num_nodes: int = 0
    num_edges: int = 0
    num_tasks: int = 0
    reward: float = 0
    action_mask: tuple[int, ...] = ()
    allowed_actions: tuple[int, ...] = ()
    valid_dirs: tuple[int, ...] = ()
    acted: int | None = None
    truncated_reason: str = "None"
    terminated_reason: str = "None"
    is_truncated: bool = False
    is_terminated: bool = False


class SimulationSnapshot(SnapshotModel):
    schema_version: Literal[1] = 1
    time: str
    frame_counter: int
    slot_counter: int
    max_slot_number: int
    period_counter: int
    max_period_numbers: int
    satellites: tuple[SatelliteSnapshot, ...]
    stations: tuple[StationSnapshot, ...]
    rois: tuple[ROISnapshot, ...]
    links: tuple[LinkSnapshot, ...]
    sun: SunSnapshot
    earth: EarthSnapshot
    tasks: tuple[TaskSnapshot, ...] = ()
    missions: tuple[PhysicalMissionSnapshot, ...] = ()
    info: RunInfo = Field(default_factory=RunInfo)


class ControlMessage(ContractModel):
    action: Literal["init", "play", "pause", "stop"]
    payload: Project | None = None
    algorithm: Literal["ophanim", "geometry", "l2d2", "phoenix", "mhspo", "ppo"] = "geometry"


class StateMessage(SnapshotModel):
    type: Literal["state"] = "state"
    state: SimulationSnapshot


class StatusMessage(SnapshotModel):
    type: Literal["status"] = "status"
    status: Literal["connected", "ready", "running", "paused", "stopped", "completed"]


class ErrorMessage(SnapshotModel):
    type: Literal["error"] = "error"
    message: str
