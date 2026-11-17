"""Consolidate existing Ophanim projects into the application's one project catalog."""
from persistence.mysql_connection import get_mysql_conn
from simulator.services.project_repository import ProjectRepository
from simulator.services.legacy_project_adapter import import_ophanim_project
from simulator.services.project_service import detect_update
from simulator.services.migration_journal import MigrationJournal


def migrate_ophanim_projects() -> int:
    repository = ProjectRepository()
    migrated_count = 0
    journal = MigrationJournal.load()
    with get_mysql_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM projects ORDER BY id")
            project_ids = [row["id"] for row in cursor.fetchall()]
            for legacy_project_id in project_ids:
                project_id = str(legacy_project_id)
                if project_id in journal.project_ids:
                    continue
                try:
                    repository.get_project(str(legacy_project_id))
                    journal.project_ids.append(project_id)
                    journal.save()
                    continue
                except FileNotFoundError:
                    pass
                cursor.execute("SELECT * FROM projects WHERE id = %s", (legacy_project_id,))
                legacy = cursor.fetchone()
                cursor.execute("SELECT id, name, latitude, longitude, altitude FROM ground_stations WHERE project_id = %s", (legacy_project_id,))
                project = import_ophanim_project(legacy_project_id, legacy, cursor.fetchall())
                repository.save_project(detect_update(project))
                journal.project_ids.append(project_id)
                journal.save()
                migrated_count += 1
    return migrated_count
