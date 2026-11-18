"""Read-only compatibility for v1 file records and failed-write recovery journals."""
import re
from pathlib import Path
from simulator.contracts import SimulationSnapshot
from simulator.services.record_contracts import RecordSnapshot, RecordWindow


def record_path(root: Path, record_id: str, suffix: str) -> Path:
    if not re.fullmatch(r"(?:[0-9a-f]{32}|timescale_[1-9][0-9]*)", record_id):
        raise ValueError("Invalid record_id")
    return root / f"{record_id}.{suffix}"


def list_records(root: Path, limit: int, project_id: str | None = None) -> list[RecordSnapshot]:
    records = []
    for path in sorted(root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        record = RecordSnapshot.model_validate_json(path.read_text())
        if project_id is None or record.project_id == project_id:
            records.append(record)
            if len(records) == limit:
                break
    return records


def get_record(root: Path, record_id: str) -> RecordSnapshot:
    return RecordSnapshot.model_validate_json(record_path(root, record_id, "json").read_text())


def get_record_window(root: Path, record_id: str, start_frame: int, frame_limit: int) -> RecordWindow:
    record = get_record(root, record_id)
    frames = []
    has_more = False
    with record_path(root, record_id, "ndjson").open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index < start_frame:
                continue
            if len(frames) >= frame_limit:
                has_more = True
                break
            frames.append(SimulationSnapshot.model_validate_json(line))
    return RecordWindow(record=record, frames=tuple(frames), start_frame=start_frame, has_more=has_more)
