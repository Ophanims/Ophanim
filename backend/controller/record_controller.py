from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from persistence.timescale_recorder import TimescaleRecorder


_recorder: Optional[TimescaleRecorder] = None
_schema_ready = False
_schema_lock = asyncio.Lock()


def _get_recorder() -> TimescaleRecorder:
    global _recorder
    if _recorder is None:
        _recorder = TimescaleRecorder()
    return _recorder


def _schema_sql_text() -> str:
    schema_path = Path(__file__).resolve().parents[1] / "sql" / "timescale_schema.sql"
    return schema_path.read_text(encoding="utf-8")


async def ensure_record_schema() -> None:
    global _schema_ready
    if _schema_ready:
        return

    async with _schema_lock:
        if _schema_ready:
            return
        recorder = _get_recorder()
        await recorder.ensure_schema(_schema_sql_text())
        _schema_ready = True


async def create_record(project_id: int, run_config: Optional[Dict[str, Any]] = None) -> int:
    await ensure_record_schema()
    recorder = _get_recorder()
    return await recorder.start_record(project_id=project_id, run_config=run_config or {})


async def append_record_state(record_id: int, project_id: int, state: Dict[str, Any]) -> None:
    recorder = _get_recorder()
    await recorder.append_state(record_id=record_id, project_id=project_id, state=state)


async def finish_record(record_id: int, status: str, error_message: Optional[str] = None) -> None:
    recorder = _get_recorder()
    await recorder.finish_record(record_id=record_id, status=status, error_message=error_message)


async def get_record(record_id: int) -> Optional[Dict[str, Any]]:
    recorder = _get_recorder()
    return await recorder.get_record(record_id)


async def list_records(project_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    recorder = _get_recorder()
    return await recorder.list_records(project_id=project_id, limit=limit)


async def get_record_series(
    record_id: int,
    state_limit: int = 5000,
    entity_limit: int = 50000,
) -> Dict[str, Any]:
    recorder = _get_recorder()
    return await recorder.get_record_series(
        record_id=record_id,
        state_limit=state_limit,
        entity_limit=entity_limit,
    )
