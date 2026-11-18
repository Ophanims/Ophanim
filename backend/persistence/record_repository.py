"""Timescale persistence for exact playback and indexed entity analysis."""
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from persistence.record_points import ENTITY_TABLES, insert_analysis_points
from simulator.contracts import SimulationSnapshot
from simulator.services.record_contracts import AnalysisPoint, AnalysisWindow, RecordSnapshot, RecordWindow


class RecordRepository:
    def __init__(self, DATABASE_URL: str | None = None, schema: str = "ophanim"):
        self.DATABASE_URL = DATABASE_URL or os.environ.get("DATABASE_URL")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required for TimescaleDB simulation records")
        self.schema = schema

    def connect(self):
        connection = psycopg.connect(self.DATABASE_URL, connect_timeout=5)
        try:
            connection.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(self.schema)))
            connection.execute("SET statement_timeout TO '15s'")
            connection.execute("SET TIME ZONE 'UTC'")
        except BaseException:
            connection.close()
            raise
        return connection

    def ensure_schema(self) -> None:
        with self.connect() as connection:
            connection.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema)))
            connection.execute((Path(__file__).resolve().parents[1] / "sql" / "record_schema.sql").read_text())

    def create_record(self, record: RecordSnapshot) -> None:
        with self.connect() as connection:
            connection.execute("INSERT INTO records (record_id, project_id, schema_version, project, code_hash, algorithm, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (record.record_id, record.project_id, record.schema_version, Jsonb(record.project.serialize()),
                 record.code_hash, record.algorithm, record.status))

    def get_record(self, record_id: str) -> RecordSnapshot:
        with self.connect() as connection:
            row = connection.cursor(row_factory=dict_row).execute("SELECT record_id, project_id, schema_version, project, code_hash, algorithm, status, frame_count FROM records WHERE record_id=%s",
                                     (record_id,)).fetchone()
        if row is None:
            raise FileNotFoundError(record_id)
        return RecordSnapshot.model_validate(row)

    def list_records(self, limit: int = 50, project_id: str | None = None) -> list[RecordSnapshot]:
        conditions = " WHERE project_id=%s" if project_id is not None else ""
        parameters = (project_id, limit) if project_id is not None else (limit,)
        with self.connect() as connection:
            rows = connection.cursor(row_factory=dict_row).execute(
                "SELECT record_id, project_id, schema_version, project, code_hash, algorithm, status, frame_count FROM records"
                + conditions + " ORDER BY created_at DESC, record_id LIMIT %s", parameters).fetchall()
        return [RecordSnapshot.model_validate(row) for row in rows]

    def append_frames(self, record_id: str, states: list[SimulationSnapshot]) -> None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany("INSERT INTO simulation_frames (time,record_id,frame_counter,payload) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    [(state.time, record_id, state.frame_counter, Jsonb(state.serialize())) for state in states])
                inserted_count = cursor.rowcount
                insert_analysis_points(cursor, record_id, states)
                cursor.execute("UPDATE records SET frame_count=frame_count+%s WHERE record_id=%s", (inserted_count, record_id))

    def close_record(self, record_id: str, status: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE records SET status=%s WHERE record_id=%s", (status, record_id))

    def get_record_window(self, record_id: str, start_frame: int, frame_limit: int) -> RecordWindow:
        with self.connect() as connection:
            # A consistent view while an active writer commits batches.
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            row = connection.cursor(row_factory=dict_row).execute("SELECT record_id, project_id, schema_version, project, code_hash, algorithm, status, frame_count FROM records WHERE record_id=%s",
                                     (record_id,)).fetchone()
            if row is None:
                raise FileNotFoundError(record_id)
            rows = connection.execute("SELECT payload FROM simulation_frames WHERE record_id=%s ORDER BY frame_counter,time OFFSET %s LIMIT %s",
                                      (record_id, start_frame, frame_limit + 1)).fetchall()
        return RecordWindow(record=RecordSnapshot.model_validate(row), start_frame=start_frame,
            frames=tuple(SimulationSnapshot.model_validate(payload) for (payload,) in rows[:frame_limit]), has_more=len(rows) > frame_limit)

    def iter_record_lines(self, record_id: str):
        with self.connect() as connection:
            with connection.cursor(name="record_download") as cursor:
                cursor.execute("SELECT payload FROM simulation_frames WHERE record_id=%s ORDER BY frame_counter,time", (record_id,))
                for (payload,) in cursor:
                    yield SimulationSnapshot.model_validate(payload).model_dump_json() + "\n"

    def delete_record(self, record_id: str) -> None:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM records WHERE record_id=%s", (record_id,))
            if not cursor.rowcount:
                raise FileNotFoundError(record_id)

    def get_analysis(self, record_id: str, entity_type: str, id: str | None,
                     start_frame: int, end_frame: int, point_limit: int, start_point: int = 0) -> AnalysisWindow:
        self.get_record(record_id)
        table = ENTITY_TABLES[entity_type]
        conditions = [sql.SQL("record_id=%s"), sql.SQL("frame_counter >= %s"), sql.SQL("frame_counter < %s")]
        parameters = [record_id, start_frame, end_frame]
        if id is not None:
            if entity_type == "links":
                conditions.append(sql.SQL("(src=%s OR dst=%s)"))
                parameters.extend((id, id))
            elif entity_type != "network":
                conditions.append(sql.SQL("id=%s"))
                parameters.append(id)
            else:
                raise ValueError("Network metrics do not have an entity id")
        order = sql.SQL("frame_counter,time")
        if entity_type == "links":
            order += sql.SQL(",type,src,dst")
        elif entity_type != "network":
            order += sql.SQL(",id")
        query = sql.SQL("SELECT time,frame_counter,payload FROM {} WHERE {} ORDER BY {} OFFSET %s LIMIT %s").format(
            sql.Identifier(table), sql.SQL(" AND ").join(conditions), order)
        with self.connect() as connection:
            rows = connection.execute(query, (*parameters, start_point, point_limit + 1)).fetchall()
        return AnalysisWindow(record_id=record_id, has_more=len(rows) > point_limit,
            start_point=start_point, next_start_point=start_point + point_limit if len(rows) > point_limit else None,
            points=tuple(AnalysisPoint(time=time.isoformat(), frame_counter=frame_counter, entity_type=entity_type, payload=payload)
                         for time, frame_counter, payload in rows[:point_limit]))
