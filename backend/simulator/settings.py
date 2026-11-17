"""Runtime paths for the integrated workspace; independent of working directory."""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
SIMULATION_DATA_DIR = Path(os.environ.get("SIMULATION_DATA_DIR", BACKEND_DIR.parent / "data" / "ophanim")).resolve()
SIMULATION_PROJECT_DIR = SIMULATION_DATA_DIR / "projects"
SIMULATION_CACHE_DIR = SIMULATION_DATA_DIR / "cache"
SIMULATION_MODEL_DIR = SIMULATION_DATA_DIR / "models"
SIMULATION_OUTPUT_DIR = SIMULATION_DATA_DIR / "output"
SIMULATION_EPHEMERIS_FILE = Path(os.environ.get("SIMULATION_EPHEMERIS_FILE", BACKEND_DIR / "de421.bsp"))


SIMULATION_TORCH_THREADS = int(os.environ.get("SIMULATION_TORCH_THREADS", "1"))
