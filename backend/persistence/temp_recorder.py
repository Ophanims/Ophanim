import asyncio
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from persistence.timescale_recorder import TimescaleRecorder

# Global in-memory map: session_id → TempSession
_sessions: Dict[str, "TempSession"] = {}
_SESSION_DIR: Optional[Path] = None


def _ensure_session_dir() -> Path:
    global _SESSION_DIR
    if _SESSION_DIR is None:
        _SESSION_DIR = Path(tempfile.mkdtemp(prefix="ophanim_sim_"))
    return _SESSION_DIR


class TempSession:
    """Holds metadata and the temp file path for one simulation session."""

    def __init__(self, project_id: int, run_config: Dict[str, Any]):
        self.session_id: str = uuid.uuid4().hex[:16]
        self.project_id: int = project_id
        self.run_config: Dict[str, Any] = run_config

        session_dir = _ensure_session_dir()
        self.file_path: Path = session_dir / f"{self.session_id}.ndjson"
        self._file_handle = open(self.file_path, "w", encoding="utf-8")
        self._closed = False

    def append_state(self, state: Dict[str, Any]) -> None:
        """Append one state dict as a JSON line."""
        if self._closed:
            return
        self._file_handle.write(json.dumps(state, ensure_ascii=False, default=str) + "\n")

    def close(self) -> None:
        """Close the file handle (discard)."""
        self._closed = True
        self._file_handle.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ── Public API ──────────────────────────────────────────────────────────

def create_session(project_id: int, run_config: Dict[str, Any]) -> str:
    """Create a new temp recording session and return its session_id."""
    session = TempSession(project_id, run_config)
    _sessions[session.session_id] = session
    return session.session_id


def get_session(session_id: str) -> Optional[TempSession]:
    return _sessions.get(session_id)


def append_state(session_id: str, state: Dict[str, Any]) -> None:
    session = _sessions.get(session_id)
    if session is not None:
        session.append_state(state)


async def save_session(session_id: str, record_status: str = "completed") -> Optional[int]:
    """Read the temp file, bulk-insert into TimescaleDB, return the record_id."""
    session = _sessions.pop(session_id, None)
    if session is None:
        return None

    session.close()

    states: List[Dict[str, Any]] = []
    try:
        with open(session.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    states.append(json.loads(line))
    except Exception:
        # If the file can't be read, clean up and return None.
        _remove_file(session.file_path)
        return None

    if not states:
        _remove_file(session.file_path)
        return None

    # Batch-insert into TimescaleDB in a single thread.
    recorder = TimescaleRecorder()
    record_id = await recorder.start_record(
        project_id=session.project_id,
        run_config=session.run_config,
    )

    for state in states:
        await recorder.append_state(
            record_id=record_id,
            project_id=session.project_id,
            state=state,
        )

    await recorder.finish_record(record_id, status=record_status)

    _remove_file(session.file_path)
    return record_id


async def discard_session(session_id: str) -> bool:
    """Delete the temp file for a session without saving."""
    session = _sessions.pop(session_id, None)
    if session is None:
        return False
    session.close()
    _remove_file(session.file_path)
    return True


def _remove_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
