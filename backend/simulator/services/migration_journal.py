"""Remember completed v0 imports, including objects subsequently deleted by users."""
import os
import tempfile
from pathlib import Path
from pydantic import Field
from simulator.schemas.base import ContractModel
from simulator.settings import SIMULATION_DATA_DIR


class MigrationJournal(ContractModel):
    schema_version: int = 1
    project_ids: list[str] = Field(default_factory=list)
    record_ids: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls):
        path = SIMULATION_DATA_DIR / "migrations.json"
        return cls.model_validate_json(path.read_text()) if path.exists() else cls()

    def save(self):
        SIMULATION_DATA_DIR.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=SIMULATION_DATA_DIR, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(self.model_dump_json(indent=2))
            os.replace(temporary, SIMULATION_DATA_DIR / "migrations.json")
        finally:
            Path(temporary).unlink(missing_ok=True)
