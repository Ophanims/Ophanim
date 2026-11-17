"""Stream historical Timescale snapshots into the application's canonical record store."""
import os
import tempfile
from pathlib import Path
import psycopg.rows
from persistence.timescale_recorder import TimescaleRecorder
from simulator.services.legacy_project_adapter import import_ophanim_project
from simulator.services.legacy_snapshot_adapter import migrate_snapshot
from simulator.services.migration_journal import MigrationJournal
from simulator.services.project_repository import ProjectRepository
from simulator.services.project_service import detect_update
from simulator.services.session_records import SIMULATION_RECORD_DIR, RecordSnapshot


def migrate_ophanim_records() -> int:
    journal = MigrationJournal.load()
    migrated_count = 0
    with TimescaleRecorder()._connect() as connection:
        with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
            cursor.execute("SELECT id, project_id, status, run_config FROM simulation_records ORDER BY id")
            rows = cursor.fetchall()
        for row in rows:
            record_id = f"timescale_{row['id']}"
            if record_id in journal.record_ids:
                continue
            try:
                current_project = ProjectRepository().get_project(str(row["project_id"]))
                stations = [{"id": station.id, "name": station.name, "latitude": station.location.lat,
                             "longitude": station.location.lon, "altitude": station.altitude_m}
                            for station in current_project.ground_stations]
            except FileNotFoundError:
                stations = []
            project = detect_update(import_ophanim_project(row["project_id"], row["run_config"], stations))
            _migrate_record(connection, row, record_id, project)
            journal.record_ids.append(record_id)
            journal.save()
            migrated_count += 1
    return migrated_count


def _migrate_record(connection, row, record_id, project):
    SIMULATION_RECORD_DIR.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=SIMULATION_RECORD_DIR, suffix=".tmp")
    frame_count = 0
    try:
        with os.fdopen(descriptor, "w") as stream:
            with connection.cursor(name=f"migration_{row['id']}") as cursor:
                cursor.execute("SELECT payload FROM simulation_state_points WHERE record_id = %s ORDER BY ts, slot_count", (row["id"],))
                for (payload,) in cursor:
                    stream.write(migrate_snapshot(payload, project).model_dump_json() + "\n")
                    frame_count += 1
        os.replace(temporary, SIMULATION_RECORD_DIR / f"{record_id}.ndjson")
        metadata = RecordSnapshot(record_id=record_id, project_id=project.project_id, project=project,
            code_hash="unknown-v0", algorithm="ophanim", status=row["status"], frame_count=frame_count)
        (SIMULATION_RECORD_DIR / f"{record_id}.json").write_text(metadata.model_dump_json())
    finally:
        Path(temporary).unlink(missing_ok=True)
