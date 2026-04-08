import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

import psycopg


class TimescaleRecorder:
    """Persist simulation record/state/entity points into TimescaleDB."""

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            raise ValueError("DATABASE_URL is required for TimescaleRecorder")

    def _connect(self):
        return psycopg.connect(self.dsn)

    async def ensure_schema(self, schema_sql: str) -> None:
        await asyncio.to_thread(self._ensure_schema_sync, schema_sql)

    def _ensure_schema_sync(self, schema_sql: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()

    async def start_record(self, project_id: int, run_config: Optional[Dict[str, Any]] = None) -> int:
        return await asyncio.to_thread(self._start_record_sync, project_id, run_config or {})

    def _start_record_sync(self, project_id: int, run_config: Dict[str, Any]) -> int:
        sql = (
            "INSERT INTO simulation_records (project_id, status, run_config) "
            "VALUES (%s, %s, %s) RETURNING id"
        )
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (project_id, "running", psycopg.types.json.Jsonb(run_config)))
                record_id = cur.fetchone()[0]
            conn.commit()
        return int(record_id)

    async def append_state(
        self,
        record_id: int,
        project_id: int,
        state: Dict[str, Any],
    ) -> None:
        await asyncio.to_thread(self._append_state_sync, record_id, project_id, state)

    def _append_state_sync(self, record_id: int, project_id: int, state: Dict[str, Any]) -> None:
        ts = self._extract_ts(state)
        sql_state = (
            "INSERT INTO simulation_state_points "
            "(ts, record_id, project_id, slot_count, timeslot, now_iso, maximum_slot, status, payload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (record_id, ts, slot_count) DO UPDATE SET "
            "payload = EXCLUDED.payload, now_iso = EXCLUDED.now_iso, status = EXCLUDED.status"
        )

        slot_count = int(state.get("slot_count", 0))
        timeslot = float(state.get("timeslot", 0.0))
        now_iso = state.get("now")
        maximum_slot = state.get("maximum_slot")
        status = state.get("status")

        entities = state.get("entities") or []

        sql_entity = (
            "INSERT INTO simulation_entity_points "
            "(ts, record_id, project_id, slot_count, entity_id, entity_type, payload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (record_id, ts, slot_count, entity_id) DO UPDATE SET "
            "payload = EXCLUDED.payload, entity_type = EXCLUDED.entity_type"
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql_state,
                    (
                        ts,
                        record_id,
                        project_id,
                        slot_count,
                        timeslot,
                        now_iso,
                        maximum_slot,
                        status,
                        psycopg.types.json.Jsonb(state),
                    ),
                )

                entity_rows = self._build_entity_rows(ts, record_id, project_id, slot_count, entities)
                if entity_rows:
                    cur.executemany(sql_entity, entity_rows)

            conn.commit()

    async def finish_record(
        self,
        record_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        await asyncio.to_thread(self._finish_record_sync, record_id, status, error_message)

    async def get_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_record_sync, record_id)

    def _get_record_sync(self, record_id: int) -> Optional[Dict[str, Any]]:
        sql = (
            "SELECT id, project_id, status, started_at, ended_at, run_config, error_message "
            "FROM simulation_records WHERE id = %s"
        )
        with self._connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, (record_id,))
                return cur.fetchone()

    async def list_records(self, project_id: int, limit: int = 50) -> list[Dict[str, Any]]:
        return await asyncio.to_thread(self._list_records_sync, project_id, limit)

    def _list_records_sync(self, project_id: int, limit: int) -> list[Dict[str, Any]]:
        sql = (
            "SELECT id, project_id, status, started_at, ended_at, run_config, error_message "
            "FROM simulation_records WHERE project_id = %s "
            "ORDER BY started_at DESC LIMIT %s"
        )
        with self._connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, (project_id, limit))
                return cur.fetchall()

    async def get_record_series(
        self,
        record_id: int,
        state_limit: int = 5000,
        entity_limit: int = 50000,
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(self._get_record_series_sync, record_id, state_limit, entity_limit)

    def _get_record_series_sync(
        self,
        record_id: int,
        state_limit: int,
        entity_limit: int,
    ) -> Dict[str, Any]:
        sql_record = (
            "SELECT id, project_id, status, started_at, ended_at, run_config, error_message "
            "FROM simulation_records WHERE id = %s"
        )
        sql_state = (
            "SELECT ts, slot_count, timeslot, now_iso, maximum_slot, status, payload "
            "FROM simulation_state_points WHERE record_id = %s "
            "ORDER BY ts ASC, slot_count ASC LIMIT %s"
        )
        sql_entity = (
            "SELECT ts, slot_count, entity_id, entity_type, payload "
            "FROM simulation_entity_points WHERE record_id = %s "
            "ORDER BY ts ASC, slot_count ASC, entity_id ASC LIMIT %s"
        )

        with self._connect() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql_record, (record_id,))
                record = cur.fetchone()

                cur.execute(sql_state, (record_id, state_limit))
                state_points = cur.fetchall()

                cur.execute(sql_entity, (record_id, entity_limit))
                entity_points = cur.fetchall()

        return {
            "record": record,
            "state_points": state_points,
            "entity_points": entity_points,
        }

    def _finish_record_sync(self, record_id: int, status: str, error_message: Optional[str]) -> None:
        sql = (
            "UPDATE simulation_records "
            "SET status = %s, ended_at = now(), error_message = %s "
            "WHERE id = %s"
        )
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (status, error_message, record_id))
            conn.commit()

    @staticmethod
    def _extract_ts(state: Dict[str, Any]) -> datetime:
        now_iso = state.get("now")
        if isinstance(now_iso, str):
            return datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
        return datetime.now(timezone.utc)

    @staticmethod
    def _build_entity_rows(
        ts: datetime,
        record_id: int,
        project_id: int,
        slot_count: int,
        entities: Iterable[Dict[str, Any]],
    ):
        rows = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            entity_id = str(
                entity.get("id")
                or entity.get("unique_id")
                or entity.get("entity_id")
                or "unknown"
            )
            entity_type = entity.get("type")
            rows.append(
                (
                    ts,
                    record_id,
                    project_id,
                    slot_count,
                    entity_id,
                    entity_type,
                    psycopg.types.json.Jsonb(entity),
                )
            )
        return rows
