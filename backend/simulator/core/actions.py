"""ID-only commands crossing the scheduling/environment boundary."""
from dataclasses import dataclass
from typing import Literal
from math import isfinite

from simulator.core.model import GeometryAction


@dataclass(frozen=True)
class SatelliteAction:
    is_processing: bool = False
    is_communicating_isl: bool = False
    is_communicating_sgl: bool = False
    update_energy: bool = True
    geometry: GeometryAction | None = None


@dataclass(frozen=True)
class StationAction:
    on_download: bool = False
    on_upload: bool = False
    geometry: GeometryAction | None = None


@dataclass(frozen=True)
class TaskAction:
    kind: Literal["age", "compute", "transfer"]
    elapsed_slots: int = 0
    nominal_slot_s: float = 1.0
    weighted_completion: bool = False
    data_bits: float = 0.0
    target_bits: float = 0.0
    dst_plane: int | None = None
    dst_order: int | None = None
    to_ground: bool = False
    acted: int | None = None


@dataclass(frozen=True)
class ComputeAction:
    task_id: int
    node_id: str


@dataclass(frozen=True)
class TransferAction:
    task_id: int
    src: str
    dst: str
    kind: Literal["isl", "sgl"]
    weight: float = 1.0

    def __post_init__(self):
        if self.kind not in {"isl", "sgl"} or not isfinite(self.weight) or self.weight <= 0:
            raise ValueError("Transfer requires a valid kind and finite positive weight")


@dataclass(frozen=True)
class SchedulingActions:
    compute: tuple[ComputeAction, ...] = ()
    transfer: tuple[TransferAction, ...] = ()


@dataclass(frozen=True)
class MissionAction:
    is_local: bool
