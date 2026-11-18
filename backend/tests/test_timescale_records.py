"""Real SQL tests. Set TEST_DATABASE_URL to a TimescaleDB instance to run them."""
import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import sql

from persistence.record_repository import RecordRepository
from simulator.core.session import SimulationSession
from simulator.defaults import default_project
from simulator.routers import records as records_router
from simulator.services.project_service import detect_update
from simulator.services.record_contracts import RecordSnapshot
from simulator.services.session_records import SessionRecord
from simulator.services.record_import import import_record_files
from simulator.schemas.ground_station import GroundStation
from simulator.schemas.base import LatLon


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "TEST_DATABASE_URL is not configured")
class TimescaleRecordTests(unittest.TestCase):
    def setUp(self):
        self.schema = "ophanim_test_" + uuid4().hex
        self.repository = RecordRepository(os.environ["TEST_DATABASE_URL"], self.schema)
        self.repository.ensure_schema()
        self.addCleanup(self.drop_schema)
        project = default_project()
        project.project_id = "timescale_test"
        project.constellation.number_of_planes = 1
        project.constellation.number_of_sat_per_planes = 2
        project.experiment.end_time = "2025-12-01T00:01:05+00:00"
        self.project = detect_update(project)
        session = SimulationSession(self.project)
        self.addCleanup(session.close)
        self.states = [session.snapshot(), session.step(), session.step()]

    def drop_schema(self):
        with self.repository.connect() as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def create_record(self):
        record = RecordSnapshot(record_id=uuid4().hex, project_id=self.project.project_id,
            project=self.project, code_hash="test", algorithm="geometry", status="running")
        self.repository.create_record(record)
        return record.record_id

    def test_roundtrip_isolation_idempotency_and_cascade_delete(self):
        first, second = self.create_record(), self.create_record()
        self.repository.append_frames(first, self.states)
        self.repository.append_frames(first, self.states)
        self.repository.append_frames(second, self.states[:1])
        self.repository.close_record(first, "completed")
        window = self.repository.get_record_window(first, 0, 2)
        self.assertTrue(window.has_more)
        self.assertEqual(3, window.record.frame_count)
        self.assertEqual("completed", window.record.status)
        self.assertEqual([state.serialize() for state in self.states[:2]], [state.serialize() for state in window.frames])
        self.assertFalse(self.repository.get_record_window(first, 2, 2).has_more)
        self.assertEqual(3, len(list(self.repository.iter_record_lines(first))))
        self.assertEqual(2, len(self.repository.list_records()))
        self.repository.delete_record(first)
        with self.repository.connect() as connection:
            for table in ("simulation_frames", "satellite_states", "station_states", "network_metrics"):
                count = connection.execute(sql.SQL("SELECT count(*) FROM {} WHERE record_id=%s").format(sql.Identifier(table)), (first,)).fetchone()[0]
                self.assertEqual(0, count)
        self.assertEqual(1, self.repository.get_record(second).frame_count)

    def test_entity_analysis_has_stable_pagination_and_real_columns(self):
        record_id = self.create_record()
        self.repository.append_frames(record_id, self.states)
        first = self.repository.get_analysis(record_id, "satellites", None, 0, 600, 1)
        second = self.repository.get_analysis(record_id, "satellites", None, 0, 600, 1, first.next_start_point)
        self.assertTrue(first.has_more)
        self.assertNotEqual(first.points[0].payload.id, second.points[0].payload.id)
        satellite = self.states[0].satellites[0]
        selected = self.repository.get_analysis(record_id, "satellites", satellite.id, 0, 600, 100)
        self.assertEqual(3, len(selected.points))
        self.assertTrue(all(point.payload.id == satellite.id for point in selected.points))
        with self.repository.connect() as connection:
            value = connection.execute("SELECT avg(battery_percent) FROM satellite_states WHERE record_id=%s AND id=%s", (record_id, satellite.id)).fetchone()[0]
        self.assertAlmostEqual(sum(state.satellites[0].battery_percent for state in self.states) / 3, value)

    def test_project_filter_is_applied_before_list_limit(self):
        record_id = self.create_record()
        other = self.project.snapshot()
        other.project_id = "other_project"
        self.repository.create_record(RecordSnapshot(record_id=uuid4().hex, project_id=other.project_id,
            project=other, code_hash="test", algorithm="geometry", status="completed"))
        selected = self.repository.list_records(1, self.project.project_id)
        self.assertEqual([record_id], [record.record_id for record in selected])
        self.assertEqual([], self.repository.list_records(1, "missing_project"))

    def test_http_playback_streaming_download_and_analysis(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("simulator.services.session_records.RecordRepository", return_value=self.repository), \
             patch("simulator.services.session_records.SIMULATION_RECOVERY_DIR", Path(directory)), \
             patch("simulator.routers.records.RecordRepository", return_value=self.repository):
            record = SessionRecord(self.project, "geometry")
            for state in self.states:
                record.append_state(state)
            record.close("completed")
            self.assertEqual([], list(Path(directory).iterdir()))
            app = FastAPI()
            app.include_router(records_router.router)
            with TestClient(app) as client:
                path = f"/records/{record.record_id}"
                playback = client.get(path, params={"frame_limit": 2})
                self.assertEqual(200, playback.status_code, playback.text)
                self.assertTrue(playback.json()["data"]["has_more"])
                download = client.get(path + "/download")
                self.assertEqual(3, len(download.text.splitlines()))
                analysis = client.get(path + "/analysis", params={"entity_type": "satellites", "id": self.states[0].satellites[0].id})
                self.assertEqual(200, analysis.status_code, analysis.text)
                self.assertEqual(3, len(analysis.json()["data"]["points"]))
                self.assertEqual(422, client.get(path + "/analysis", params={"entity_type": "arbitrary_table"}).status_code)
                self.assertEqual(200, client.delete(path).status_code)
                self.assertEqual(404, client.get(path).status_code)

    def test_recovery_import_does_not_duplicate_partially_committed_frames(self):
        record_id = self.create_record()
        self.repository.append_frames(record_id, self.states[:1])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = self.repository.get_record(record_id)
            (root / f"{record_id}.json").write_text(metadata.model_dump_json())
            (root / f"{record_id}.ndjson").write_text("\n".join(state.model_dump_json() for state in self.states) + "\n")
            self.assertEqual(1, import_record_files(root, self.repository))
            self.assertEqual(1, import_record_files(root, self.repository))
            self.assertEqual("interrupted", self.repository.get_record(record_id).status)
            self.repository.close_record(record_id, "completed")
            self.assertEqual(1, import_record_files(root, self.repository))
        self.assertEqual(3, self.repository.get_record(record_id).frame_count)
        self.assertEqual("completed", self.repository.get_record(record_id).status)

    def test_all_entity_types_persist_through_the_unchanged_algorithms(self):
        project = self.project.snapshot()
        project.ground_stations = [GroundStation(id="station", project_id=project.project_id,
            name="Station", location=LatLon(lat=0, lon=0))]
        for algorithm in ("ophanim", "l2d2", "phoenix", "mhspo"):
            with self.subTest(algorithm=algorithm):
                session = SimulationSession(project, algorithm)
                try:
                    state = session.step()
                    record = RecordSnapshot(record_id=uuid4().hex, project_id=project.project_id,
                        project=project, code_hash="test", algorithm=algorithm, status="running")
                    self.repository.create_record(record)
                    self.repository.append_frames(record.record_id, [state])
                    for kind, expected in (("satellites", state.satellites), ("stations", state.stations),
                                           ("tasks", state.tasks), ("missions", state.missions), ("links", state.links)):
                        window = self.repository.get_analysis(record.record_id, kind, None, 0, 600, 10000)
                        self.assertEqual(len(expected), len(window.points), kind)
                        expected_payloads = sorted((item.model_dump(mode="json") for item in expected), key=str)
                        actual_payloads = sorted((point.payload.model_dump(mode="json") for point in window.points), key=str)
                        self.assertEqual(expected_payloads, actual_payloads)
                finally:
                    session.close()
