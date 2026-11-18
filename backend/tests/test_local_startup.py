"""Startup checks the configured record database before accepting simulations."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from simulator.services.project_repository import ProjectRepository
from persistence.record_repository import RecordRepository


class LocalStartupTests(unittest.TestCase):
    def test_startup_initializes_record_schema_and_keeps_file_projects(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True), \
             patch("main.SIMULATION_DATA_DIR", Path(directory)), \
             patch("main.RecordRepository") as records, \
             patch("simulator.routers.project.repository", ProjectRepository(Path(directory) / "projects")):
            with TestClient(app) as client:
                self.assertEqual({"ok": True}, client.get("/health").json())
                self.assertEqual([], client.get("/api/projects").json()["data"])
            records.return_value.ensure_schema.assert_called_once()

    def test_missing_database_configuration_fails_explicitly(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "DATABASE_URL"):
                RecordRepository()
