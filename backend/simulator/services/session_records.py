"""Append canonical snapshots to disk; read bounded windows for history playback."""
import json
import hashlib
from functools import lru_cache
import os
import re
import tempfile
from pathlib import Path
from typing import Literal
from uuid import uuid4
from pydantic import Field
from simulator.contracts import SimulationSnapshot
from simulator.schemas.base import SnapshotModel
from simulator.schemas.project import Project
from simulator.settings import SIMULATION_DATA_DIR

SIMULATION_RECORD_DIR = SIMULATION_DATA_DIR / "records"


class RecordSnapshot(SnapshotModel):
    schema_version: Literal[1] = 1
    record_id: str
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


@lru_cache(maxsize=1)
def source_code_hash() -> str:
    digest = hashlib.sha256()
    root = Path(__file__).resolve().parents[2]
    for path in sorted(root.rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class SessionRecord:
    def __init__(self, project: Project, algorithm: str):
        SIMULATION_RECORD_DIR.mkdir(parents=True, exist_ok=True)
        self.record_id = uuid4().hex
        self.project = project.snapshot()
        self.project_id = project.project_id
        self.algorithm = algorithm
        self.status = "running"
        self.frame_count = 0
        self._stream = (SIMULATION_RECORD_DIR / f"{self.record_id}.ndjson").open("w", encoding="utf-8")
        self._write_metadata()

    def snapshot(self) -> RecordSnapshot:
        return RecordSnapshot(record_id=self.record_id, project_id=self.project_id, project=self.project.snapshot(), code_hash=source_code_hash(), algorithm=self.algorithm,
                              status=self.status, frame_count=self.frame_count)

    def _write_metadata(self) -> None:
        descriptor, temporary = tempfile.mkstemp(dir=SIMULATION_RECORD_DIR, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(self.snapshot().model_dump_json())
            os.replace(temporary, SIMULATION_RECORD_DIR / f"{self.record_id}.json")
        finally:
            Path(temporary).unlink(missing_ok=True)

    def append_state(self, state: SimulationSnapshot) -> None:
        self._stream.write(state.model_dump_json() + "\n")
        self._stream.flush()
        self.frame_count += 1

    def close(self, status: str) -> None:
        self.status = status
        self._stream.close()
        self._write_metadata()


def list_records(limit: int = 50) -> list[RecordSnapshot]:
    return [RecordSnapshot.model_validate_json(path.read_text())
            for path in sorted(SIMULATION_RECORD_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]]


def record_path(record_id: str, suffix: str) -> Path:
    if not re.fullmatch(r"(?:[0-9a-f]{32}|timescale_[1-9][0-9]*)", record_id):
        raise ValueError("Invalid record_id")
    return SIMULATION_RECORD_DIR / f"{record_id}.{suffix}"


def get_record_window(record_id: str, start_frame: int, frame_limit: int) -> RecordWindow:
    record = RecordSnapshot.model_validate_json(record_path(record_id, "json").read_text())
    frames = []
    has_more = False
    with record_path(record_id, "ndjson").open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index < start_frame:
                continue
            if len(frames) >= frame_limit:
                has_more = True
                break
            frames.append(SimulationSnapshot.model_validate_json(line))
    return RecordWindow(record=record, frames=tuple(frames), start_frame=start_frame, has_more=has_more)


def delete_record(record_id: str) -> None:
    record_path(record_id, "json").unlink()
    record_path(record_id, "ndjson").unlink(missing_ok=True)
