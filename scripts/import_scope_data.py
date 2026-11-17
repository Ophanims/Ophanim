"""One-time, offline SCOPE project/checkpoint import; never used by HTTP APIs."""
import argparse
import hashlib
import json
import pickle
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from simulator.schemas.project import Project
from simulator.services.project_repository import ProjectRepository
from simulator.services.project_service import detect_update
from simulator.settings import SIMULATION_MODEL_DIR


class LegacyRecord:
    def __setstate__(self, state):
        self.__dict__.update(state.get("__dict__", state))


class ProjectUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith(("app.models.api_dict.", "models.api_dict.")):
            return LegacyRecord
        if module == "builtins" and name in {"set", "frozenset"}:
            return {"set": set, "frozenset": frozenset}[name]
        raise pickle.UnpicklingError(f"Unsupported legacy project class: {module}.{name}")


FIELD_NAMES = {
    "userId": "user_id", "groundStations": "ground_stations", "projectId": "project_id",
    "numberOfPlanes": "number_of_planes", "numberOfSatPerPlanes": "number_of_sat_per_planes",
    "phaseFactor": "phase_factor", "orbitalPeriod": "orbital_period", "startTime": "start_time",
    "endTime": "end_time", "timeSlot": "time_slot", "targetId": "target_id",
    "sourceNodeId": "source_node_id", "endNodeId": "end_node_id", "constellationId": "constellation_id",
    "focalLength": "focal_length_mm", "widthPx": "width_px", "lengthPx": "length_px",
    "pxSizeWidth": "px_size_width", "pxSizeLength": "px_size_length",
    "channelsPerPx": "channels_per_pixel", "bitsPerChannel": "bits_per_channel",
}
for direction in ("downlink", "uplink", "isl"):
    for old, new in {"FrequencyHz": "frequency_hz", "BandwidthHz": "bandwidth_hz",
                     "TxPowerW": "tx_power_w", "GainTxDbi": "gain_tx_dbi",
                     "GainRxDbi": "gain_rx_dbi", "NoiseTempK": "noise_temp_k"}.items():
        FIELD_NAMES[direction + old] = direction + "_" + new


def normalize_legacy(value):
    if isinstance(value, LegacyRecord):
        value = value.__dict__
    if isinstance(value, dict):
        return {FIELD_NAMES.get(key, key): normalize_legacy(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_legacy(item) for item in value]
    return value


def import_projects(source: Path) -> int:
    repository = ProjectRepository()
    imported_count = 0
    for file_path in sorted((source / "backend/projects").glob("*.pkl")):
        with file_path.open("rb") as stream:
            project_data = normalize_legacy(ProjectUnpickler(stream).load())
        project_data["project_id"] = project_data.pop("id")
        project_data["title"] = project_data.get("title") or "Imported project"
        project_data["description"] = project_data.get("description") or ""
        project = Project.model_validate(project_data)
        destination = repository._path(project.project_id)
        if destination.exists():
            if repository.get_project(project.project_id).serialize() != project.serialize():
                raise FileExistsError(f"Import would overwrite an existing project: {project.project_id}")
            continue
        repository.save_project(project)
        imported_count += 1
    return imported_count


def import_models(source: Path) -> int:
    imported_count = 0
    model_source = source / "backend/ai_model"
    for file_path in model_source.rglob("*"):
        if file_path.suffix not in {".zip", ".vecnormalize"}:
            continue
        destination = SIMULATION_MODEL_DIR / file_path.relative_to(model_source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).digest() != hashlib.sha256(file_path.read_bytes()).digest():
                raise FileExistsError(f"Model already exists with different content: {destination.name}")
            continue
        shutil.copy2(file_path, destination)
        imported_count += 1
    return imported_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--models", action="store_true")
    arguments = parser.parse_args()
    print(f"Imported projects: {import_projects(arguments.source)}")
    if arguments.models:
        print(f"Imported model files: {import_models(arguments.source)}")
