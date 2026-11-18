"""Record canonical snapshots in TimescaleDB, retaining a journal until committed."""
import hashlib
import logging
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from persistence.record_repository import RecordRepository
from simulator.contracts import SimulationSnapshot
from simulator.schemas.project import Project
from simulator.services import record_files
from simulator.services.record_contracts import RecordSnapshot, RecordWindow
from simulator.services.record_writer import RecordWriter
from simulator.settings import SIMULATION_DATA_DIR

SIMULATION_RECORD_DIR = SIMULATION_DATA_DIR / "records"
SIMULATION_RECOVERY_DIR = SIMULATION_DATA_DIR / "record_recovery"
logger = logging.getLogger(__name__)


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
        self.record_id = uuid4().hex
        self.project = project.snapshot()
        self.project_id = project.project_id
        self.algorithm = algorithm
        self.status = "running"
        self.frame_count = 0
        self._closed = False
        self.repository = RecordRepository()
        self.repository.create_record(self.snapshot())
        SIMULATION_RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
        self._stream = record_files.record_path(SIMULATION_RECOVERY_DIR, self.record_id, "ndjson").open("w", encoding="utf-8")
        self._write_metadata()
        self.writer = RecordWriter(self.repository, self.record_id)

    def snapshot(self) -> RecordSnapshot:
        return RecordSnapshot(record_id=self.record_id, project_id=self.project_id, project=self.project.snapshot(),
            code_hash=source_code_hash(), algorithm=self.algorithm, status=self.status, frame_count=self.frame_count)

    def _write_metadata(self) -> None:
        descriptor, temporary = tempfile.mkstemp(dir=SIMULATION_RECOVERY_DIR, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(self.snapshot().model_dump_json())
            os.replace(temporary, record_files.record_path(SIMULATION_RECOVERY_DIR, self.record_id, "json"))
        finally:
            Path(temporary).unlink(missing_ok=True)

    def append_state(self, state: SimulationSnapshot) -> None:
        if self._closed:
            raise ValueError("Record is closed")
        self.writer.check()
        self._stream.write(state.model_dump_json() + "\n")
        self._stream.flush()
        self.frame_count += 1
        self.writer.append(state)

    def close(self, status: str) -> None:
        if self._closed:
            return
        self._closed = True
        self.status = status
        self._stream.close()
        try:
            self.writer.finish()
            self.repository.close_record(self.record_id, status)
        except Exception:
            self.status = "failed"
            self._write_metadata()
            try:
                self.repository.close_record(self.record_id, "failed")
            except Exception:
                logger.exception("Could not mark failed record in TimescaleDB; recovery journal retained",
                                 extra={"record_id": self.record_id})
            raise
        self._write_metadata()
        record_files.record_path(SIMULATION_RECOVERY_DIR, self.record_id, "ndjson").unlink()
        record_files.record_path(SIMULATION_RECOVERY_DIR, self.record_id, "json").unlink()


def record_path(record_id: str, suffix: str) -> Path:
    return record_files.record_path(SIMULATION_RECORD_DIR, record_id, suffix)


def list_records(limit: int = 50, project_id: str | None = None) -> list[RecordSnapshot]:
    records = RecordRepository().list_records(limit, project_id)
    known = {record.record_id for record in records}
    records.extend(record for record in record_files.list_records(SIMULATION_RECORD_DIR, limit, project_id)
                   if record.record_id not in known)
    return records[:limit]


def get_record(record_id: str) -> RecordSnapshot:
    try:
        return RecordRepository().get_record(record_id)
    except FileNotFoundError:
        return record_files.get_record(SIMULATION_RECORD_DIR, record_id)


def get_record_window(record_id: str, start_frame: int, frame_limit: int) -> RecordWindow:
    try:
        return RecordRepository().get_record_window(record_id, start_frame, frame_limit)
    except FileNotFoundError:
        return record_files.get_record_window(SIMULATION_RECORD_DIR, record_id, start_frame, frame_limit)


def iter_record_lines(record_id: str):
    try:
        RecordRepository().get_record(record_id)
    except FileNotFoundError:
        with record_path(record_id, "ndjson").open(encoding="utf-8") as stream:
            yield from stream
    else:
        yield from RecordRepository().iter_record_lines(record_id)


def delete_record(record_id: str) -> None:
    try:
        RecordRepository().delete_record(record_id)
    except FileNotFoundError:
        record_path(record_id, "json").unlink()
        record_path(record_id, "ndjson").unlink(missing_ok=True)
    else:
        # A migrated file must not reappear after its database copy is deleted.
        record_path(record_id, "json").unlink(missing_ok=True)
        record_path(record_id, "ndjson").unlink(missing_ok=True)
