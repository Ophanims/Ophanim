"""Regressions for sharing one catalog, contract and session across both codebases."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from simulator.defaults import default_project
from simulator.services.project_service import detect_update
from simulator.core.session import SimulationSession
from simulator.services.legacy_snapshot_adapter import migrate_snapshot
from simulator.services.project_repository import ProjectRepository
from simulator.services.project_migration import migrate_ophanim_projects
from simulator.services.migration_journal import MigrationJournal
from simulator.services import session_records
from record_test_support import MemoryRecordRepository


def short_project(seed=0):
    project = default_project()
    project.project_id = "shared_project"
    project.seed = seed
    project.experiment.end_time = "2025-12-01T00:01:05+00:00"
    return detect_update(project)


class UnifiedApplicationTests(unittest.TestCase):
    def test_engines_share_the_default_end_time(self):
        project = short_project()
        project.experiment.end_time = None
        physics = SimulationSession(project, "ophanim")
        geometry = SimulationSession(project, "geometry")
        try:
            self.assertEqual(geometry.environment.t_end, physics.environment.t_end)
            self.assertEqual(geometry.snapshot().max_period_numbers, physics.snapshot().max_period_numbers)
        finally:
            physics.close()
            geometry.close()

    def test_physics_sessions_are_independent_and_snapshot_is_pure(self):
        project = short_project()
        first = SimulationSession(project, "ophanim")
        unrelated = SimulationSession(short_project(123), "ophanim")
        reference = SimulationSession(project, "ophanim")
        try:
            initial = first.snapshot().serialize()
            self.assertEqual(initial, first.snapshot().serialize())
            for _ in range(3):
                unrelated.step()
                self.assertEqual(first.step().serialize(), reference.step().serialize())
            self.assertTrue(first.is_completed)
            self.assertEqual(project.experiment.end_time, first.snapshot().time)
            self.assertTrue(first.snapshot().info.is_terminated)
            self.assertEqual(0, initial["frame_counter"])
            self.assertEqual((), initial["missions"] if isinstance(initial["missions"], tuple) else tuple(initial["missions"]))
            self.assertTrue(all(mission.position in {satellite.id for satellite in first.snapshot().satellites}
                                for mission in first.snapshot().missions))
        finally:
            for session in (first, unrelated, reference):
                session.close()

    def test_physics_and_geometry_use_the_same_orbits_and_ids(self):
        project = short_project()
        physics = SimulationSession(project, "ophanim")
        geometry = SimulationSession(project, "geometry")
        try:
            for _ in range(2):
                for physical, geometric in zip(physics.snapshot().satellites, geometry.snapshot().satellites):
                    self.assertEqual(physical.id, geometric.id)
                    for axis in "xyz":
                        self.assertAlmostEqual(getattr(physical.pos, axis), getattr(geometric.pos, axis), delta=1)
                physics.step()
                geometry.step()
        finally:
            physics.close()
            geometry.close()

    def test_existing_project_keeps_id_and_deletion_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = ProjectRepository(Path(directory) / "projects")
            cursor = MagicMock()
            cursor.fetchall.side_effect = [[{"id": 7}], [], [{"id": 7}]]
            cursor.fetchone.return_value = {"name": "Existing project", "maximumNumberOfPlane": 1,
                "sizeOfConstellation": 1, "startTime": "2025-12-01T00:00:00+00:00",
                "endTime": "2025-12-01T00:01:05+00:00", "batteryCapacityWh": 80}
            connection = MagicMock()
            connection.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor
            with patch("simulator.services.project_migration.get_mysql_conn", return_value=connection), \
                 patch("simulator.services.project_migration.ProjectRepository", return_value=repository), \
                 patch("simulator.services.migration_journal.SIMULATION_DATA_DIR", Path(directory)):
                self.assertEqual(1, migrate_ophanim_projects())
                self.assertEqual("ophanim", repository.get_project("7").algorithm)
                self.assertEqual(80, repository.get_project("7").resources.battery_capacity_wh)
                repository.delete_project("7")
                self.assertEqual(0, migrate_ophanim_projects())
                self.assertEqual([], repository.list_projects())
                self.assertEqual(["7"], MigrationJournal.load().project_ids)

    def test_v0_history_uses_the_same_record_window_contract(self):
        project = short_project()
        state = migrate_snapshot({"clock": {"current_datetime": project.experiment.start_time,
            "slot_count": 0, "maximum_slot": 3}, "entities": [], "links": [], "missions": []}, project)
        with tempfile.TemporaryDirectory() as directory, patch.object(session_records, "SIMULATION_RECORD_DIR", Path(directory)), \
             patch.object(session_records, "RecordRepository", return_value=MemoryRecordRepository()):
            record_id = "timescale_7"
            metadata = session_records.RecordSnapshot(record_id=record_id, project_id=project.project_id,
                project=project, algorithm="ophanim", code_hash="unknown-v0", status="completed", frame_count=1)
            session_records.record_path(record_id, "json").write_text(metadata.model_dump_json())
            session_records.record_path(record_id, "ndjson").write_text(state.model_dump_json() + "\n")
            window = session_records.get_record_window(record_id, 0, 600)
            self.assertEqual(state.serialize(), window.frames[0].serialize())
            self.assertFalse(window.has_more)
            session_records.delete_record(record_id)
            self.assertEqual([], session_records.list_records())


if __name__ == "__main__":
    unittest.main()
