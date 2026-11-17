"""Immutable checkpoint runs and an atomic per-project latest pointer."""
import json
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4
from simulator.settings import SIMULATION_MODEL_DIR


def project_model_directory(project_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", project_id):
        raise ValueError("Save the project before training")
    return SIMULATION_MODEL_DIR / "projects" / project_id


def create_training_path(project_id: str) -> str:
    directory = project_model_directory(project_id) / "runs" / uuid4().hex
    directory.mkdir(parents=True)
    return str(directory / "final_ppo_leoenv")


def model_path_for_project(project_id: str) -> str:
    pointer = project_model_directory(project_id) / "latest.json"
    if not pointer.exists():
        return str(SIMULATION_MODEL_DIR / "final_ppo_leoenv")
    run_id = json.loads(pointer.read_text())["run_id"]
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise ValueError("Invalid model run_id")
    return str(pointer.parent / "runs" / run_id / "final_ppo_leoenv")


def publish_checkpoint(project_id: str, model_path: str) -> None:
    model_path = Path(model_path)
    directory = project_model_directory(project_id)
    if model_path.parent.parent != directory / "runs":
        raise ValueError("Checkpoint does not belong to this project")
    for suffix in (".zip", ".vecnormalize"):
        if not Path(str(model_path) + suffix).is_file():
            raise FileNotFoundError("Checkpoint and normalizer must both be saved before publishing")
    descriptor, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"run_id": model_path.parent.name}, stream)
        os.replace(temporary, directory / "latest.json")
    finally:
        Path(temporary).unlink(missing_ok=True)
