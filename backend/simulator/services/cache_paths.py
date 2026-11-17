"""Cache keys include the entire contract, timeline and format version."""
import hashlib
import json
from datetime import datetime
from simulator.settings import SIMULATION_CACHE_DIR
from simulator.schemas.project import Project


def cache_path_for(kind: str, datetimes: list[datetime], project: Project | None = None) -> str:
    descriptor = {"schema_version": 2, "kind": kind,
                  "datetimes": [value.isoformat() for value in datetimes],
                  "project": project.serialize() if project is not None else None}
    fingerprint = hashlib.sha256(json.dumps(descriptor, sort_keys=True).encode()).hexdigest()
    return str(SIMULATION_CACHE_DIR / kind / f"{fingerprint}.pkl")
