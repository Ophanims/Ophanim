"""Idempotently restore file records through the canonical Timescale write path."""
from pathlib import Path
from simulator.contracts import SimulationSnapshot
from simulator.services.record_contracts import RecordSnapshot


def import_record_files(directory: Path, repository) -> int:
    imported_count = 0
    for path in sorted(directory.glob("*.json")):
        record = RecordSnapshot.model_validate_json(path.read_text())
        frames = path.with_suffix(".ndjson")
        if not frames.is_file():
            raise FileNotFoundError(frames)
        try:
            existing = repository.get_record(record.record_id)
        except FileNotFoundError:
            existing = None
            repository.create_record(record.model_copy(update={"status": "importing", "frame_count": 0}))
        batch = []
        with frames.open(encoding="utf-8") as stream:
            for line in stream:
                batch.append(SimulationSnapshot.model_validate_json(line))
                if len(batch) == 16:
                    repository.append_frames(record.record_id, batch)
                    batch = []
        if batch:
            repository.append_frames(record.record_id, batch)
        status = "interrupted" if record.status == "running" else record.status
        if existing is not None and record.status == "running" and existing.status in {"completed", "stopped", "disconnected"}:
            # A crash may leave the initial journal metadata after the final
            # database commit; recovery must not downgrade a finished record.
            status = existing.status
        repository.close_record(record.record_id, status)
        imported_count += 1
    return imported_count
