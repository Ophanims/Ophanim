"""Manage only derived, content-addressed data owned by this module."""
from pathlib import Path
import shutil
from simulator.core.initialisation import load_input_metadata
from simulator.schemas.project import Project
from simulator.settings import SIMULATION_CACHE_DIR


def get_cache_folder_size() -> int:
    return sum(path.stat().st_size for path in SIMULATION_CACHE_DIR.rglob("*.pkl") if path.is_file())


def clear_cache_folder() -> None:
    # No caller-controlled directory; project and model storage are never touched.
    if SIMULATION_CACHE_DIR.exists():
        shutil.rmtree(SIMULATION_CACHE_DIR)


def initial_cache_setup(project: Project) -> None:
    from simulator.core.initialisation import build_static_objects
    from simulator.services.project_service import detect_update
    project = detect_update(project)
    metadata = load_input_metadata(project, 7200)
    build_static_objects(project, metadata["period"], metadata["max_period_numbers"], metadata["datetime_list"])


def check_all_cache_integrity(project: Project) -> dict[str, bool]:
    from simulator.services.cache_paths import cache_path_for
    metadata = load_input_metadata(project, 7200)
    return {kind: Path(cache_path_for(kind, metadata["datetime_list"], project if kind in {"satellites", "stations", "rois"} else None)).is_file()
            for kind in ("satellites", "stations", "rois", "earth", "sun")}
