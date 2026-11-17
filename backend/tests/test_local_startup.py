"""The application must run with no database environment or server."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from simulator.services.project_repository import ProjectRepository


class LocalStartupTests(unittest.TestCase):
    def test_startup_and_projects_without_database_configuration(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True), \
             patch("main.SIMULATION_DATA_DIR", Path(directory)), \
             patch("simulator.routers.project.repository", ProjectRepository(Path(directory) / "projects")):
            with TestClient(app) as client:
                self.assertEqual({"ok": True}, client.get("/health").json())
                self.assertEqual([], client.get("/api/projects").json()["data"])
