"""Contract, persistence, temporal consistency and transport regression tests."""
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from simulator.api import router
from simulator.contracts import ControlMessage, SimulationSnapshot
from simulator.core.initialisation import load_input_metadata, normalize_time
from simulator.core.session import SimulationSession
from simulator.defaults import default_project
from simulator.schemas.project import Project
from simulator.routers import project as project_router
from simulator.services.cache_paths import cache_path_for
from simulator.services.legacy_project_adapter import import_ophanim_project
from simulator.services.project_repository import ProjectRepository
from simulator.services.project_service import detect_update
from simulator.services.session_records import SessionRecord, get_record_window


def test_project():
    project = default_project()
    project.project_id = "integration_test"
    project.constellation.number_of_planes = 2
    project.constellation.number_of_sat_per_planes = 3
    project.experiment.end_time = (normalize_time(project.experiment.start_time) + timedelta(seconds=65)).isoformat()
    return detect_update(project)


class ScopeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.repository = ProjectRepository(self.root / "projects")
        for location, value in [
            ("simulator.services.cache_paths.SIMULATION_CACHE_DIR", self.root / "cache"),
            ("simulator.services.session_records.SIMULATION_RECORD_DIR", self.root / "records"),
            ("simulator.routers.project.repository", self.repository),
        ]:
            patcher = patch(location, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_contract_rejects_aliases_and_nonfinite_values(self):
        data = default_project().serialize()
        data["projectId"] = data.pop("project_id")
        with self.assertRaises(ValidationError):
            Project.model_validate(data)
        data = default_project().serialize()
        data["constellation"]["altitude"] = float("nan")
        with self.assertRaises(ValidationError):
            Project.model_validate(data)
        with self.assertRaises(ValidationError):
            ControlMessage(action="unknown")

    def test_json_repository_roundtrip_and_path_boundaries(self):
        project = test_project()
        saved = self.repository.save_project(project)
        self.assertEqual(saved.serialize(), self.repository.get_project(project.project_id).serialize())
        self.assertEqual(1, len(self.repository.list_projects()))
        with self.assertRaises(ValueError):
            self.repository.get_project("../escape")
        self.repository.delete_project(project.project_id)
        with self.assertRaises(FileNotFoundError):
            self.repository.get_project(project.project_id)

    def test_cache_key_changes_with_configuration_and_timeline(self):
        project = test_project()
        metadata = load_input_metadata(project, 7200)
        before = cache_path_for("satellites", metadata["datetime_list"], project)
        project.hardware.width_px += 1
        self.assertNotEqual(before, cache_path_for("satellites", metadata["datetime_list"], project))
        shifted = [value + timedelta(days=1) for value in metadata["datetime_list"]]
        self.assertNotEqual(cache_path_for("earth", metadata["datetime_list"]), cache_path_for("earth", shifted))

    def test_geometry_snapshot_isolation_and_exact_end_time(self):
        project = test_project()
        session = SimulationSession(project)
        self.addCleanup(session.close)
        other = SimulationSession(project)
        self.addCleanup(other.close)
        first = session.snapshot()
        second = session.step()
        self.assertNotEqual(first.time, second.time)
        self.assertEqual(first.time, other.snapshot().time)
        self.assertEqual(first.serialize(), SimulationSnapshot.model_validate_json(first.model_dump_json()).serialize())
        first.satellites[0].img_corners_pos.clear()
        self.assertEqual(4, len(session.snapshot().satellites[0].img_corners_pos))
        while not session.is_completed:
            session.step()
        self.assertEqual(normalize_time(project.experiment.end_time), normalize_time(session.snapshot().time))
        self.assertEqual(session.snapshot().serialize(), session.step().serialize())

    def test_records_use_the_exact_live_snapshot_and_bounded_windows(self):
        project = test_project()
        session = SimulationSession(project)
        self.addCleanup(session.close)
        record = SessionRecord(project, "geometry")
        expected = [session.snapshot(), session.step(), session.step()]
        for state in expected:
            record.append_state(state)
        record.close("completed")
        window = get_record_window(record.record_id, 0, 2)
        self.assertTrue(window.has_more)
        self.assertEqual([state.serialize() for state in expected[:2]], [state.serialize() for state in window.frames])
        final = get_record_window(record.record_id, 2, 2)
        self.assertFalse(final.has_more)
        self.assertEqual(3, final.record.frame_count)

    def test_project_http_crud_and_validation(self):
        response = self.client.post("/api/projects", json=test_project().serialize())
        self.assertEqual(200, response.status_code, response.text)
        data = response.json()["data"]
        self.assertIn("project_id", data)
        self.assertNotIn("projectId", data)
        self.assertEqual(1, len(self.client.get("/api/projects").json()["data"]))
        self.assertEqual(404, self.client.get("/api/projects/missing").status_code)
        self.assertEqual(200, self.client.delete(f"/api/projects/{data['project_id']}").status_code)
        self.assertEqual(404, self.client.delete(f"/api/projects/{data['project_id']}").status_code)
        invalid = test_project().serialize()
        invalid["constellation"]["number_of_planes"] = 0
        self.assertEqual(422, self.client.post("/api/projects", json=invalid).status_code)

    def test_websocket_controls_and_final_snapshot(self):
        with self.client.websocket_connect("/api/simulation/ws") as socket:
            self.assertEqual("connected", socket.receive_json()["status"])
            socket.send_json({"action": "play"})
            self.assertEqual("error", socket.receive_json()["type"])
            socket.send_json({"action": "init", "payload": test_project().serialize(), "algorithm": "geometry"})
            initial = socket.receive_json()
            self.assertEqual("state", initial["type"])
            self.assertEqual("ready", socket.receive_json()["status"])
            socket.send_json({"action": "pause"})
            self.assertEqual("paused", socket.receive_json()["status"])
            socket.send_json({"action": "play"})
            self.assertEqual("running", socket.receive_json()["status"])
            messages = []
            while True:
                message = socket.receive_json()
                messages.append(message)
                if message.get("status") == "completed":
                    break
            states = [message["state"] for message in messages if message["type"] == "state"]
            self.assertEqual(test_project().experiment.end_time, states[-1]["time"])
            socket.send_json({"action": "stop"})
            self.assertEqual("stopped", socket.receive_json()["status"])
        records = self.client.get("/api/records").json()["data"]
        self.assertEqual(1, len(records))
        self.assertEqual("completed", records[0]["status"])

    def test_legacy_import_converts_units_and_identifiers(self):
        project = import_ophanim_project(7, {
            "name": "Legacy", "sizeOfConstellation": 6, "maximumNumberOfPlane": 2,
            "carrierFrequencyOfIslGhz": 26, "bandwidthOfIslMhz": 20,
        }, [{"id": 3, "name": "Station", "latitude": 20, "longitude": 100}])
        self.assertEqual("7", project.project_id)
        self.assertEqual(26e9, project.hardware.isl_frequency_hz)
        self.assertEqual(20e6, project.hardware.isl_bandwidth_hz)
        self.assertEqual(3, project.constellation.number_of_sat_per_planes)
        self.assertEqual("7", project.ground_stations[0].project_id)


if __name__ == "__main__":
    unittest.main()
