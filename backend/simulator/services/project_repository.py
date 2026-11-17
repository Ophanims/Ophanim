"""Atomic JSON storage using exactly the project contract field names."""

import os
import re
import tempfile
from pathlib import Path
from simulator.schemas.project import Project
from simulator.settings import SIMULATION_PROJECT_DIR


class ProjectRepository:
    def __init__(self, SIMULATION_PROJECT_DIR: Path = SIMULATION_PROJECT_DIR):
        self.SIMULATION_PROJECT_DIR = Path(SIMULATION_PROJECT_DIR)

    def _path(self, project_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", project_id):
            raise ValueError("Invalid project_id")
        return self.SIMULATION_PROJECT_DIR / f"{project_id}.json"

    def save_project(self, project: Project) -> Project:
        destination = self._path(project.project_id)
        self.SIMULATION_PROJECT_DIR.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.SIMULATION_PROJECT_DIR, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(project.model_dump_json(indent=2))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return project.snapshot()

    def get_project(self, project_id: str) -> Project:
        return Project.model_validate_json(self._path(project_id).read_text(encoding="utf-8"))

    def list_projects(self) -> list[Project]:
        if not self.SIMULATION_PROJECT_DIR.exists():
            return []
        return [Project.model_validate_json(path.read_text(encoding="utf-8"))
                for path in sorted(self.SIMULATION_PROJECT_DIR.glob("*.json"))]

    def delete_project(self, project_id: str) -> None:
        self._path(project_id).unlink()

