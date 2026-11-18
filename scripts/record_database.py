"""Configure the record database and start the optional local Timescale service."""
import os
import shutil
import subprocess
import time
from pathlib import Path

from psycopg import OperationalError, connect
from psycopg.conninfo import make_conninfo

ROOT = Path(__file__).resolve().parents[1]


def configure_record_database() -> bool:
    """Return whether credentials select the managed local database."""
    if os.environ.get("DATABASE_URL"):
        return False
    missing = [key for key in ("DB_USER", "DB_PASSWORD", "DB_NAME") if not os.environ.get(key)]
    if missing:
        raise RuntimeError("Set DATABASE_URL or configure " + ", ".join(missing) + " in .env")
    os.environ["DATABASE_URL"] = make_conninfo(
        host="127.0.0.1", port=os.environ.get("DB_PORT", "15432"),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], dbname=os.environ["DB_NAME"])
    return True


def database_ready() -> bool:
    try:
        with connect(os.environ["DATABASE_URL"], connect_timeout=2):
            return True
    except OperationalError:
        return False


def start_record_database(managed: bool) -> None:
    if database_ready():
        return
    if not managed:
        raise RuntimeError("Cannot connect to DATABASE_URL; start the configured TimescaleDB service.")
    if not shutil.which("docker"):
        raise RuntimeError("Docker is needed for the local TimescaleDB service, or set DATABASE_URL.")
    try:
        result = subprocess.run(["docker", "compose", "--project-directory", str(ROOT),
            "-f", str(ROOT / "compose.records.yml"), "up", "-d"], timeout=120, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("TimescaleDB startup timed out; check Docker Desktop.") from error
    if result.returncode:
        raise RuntimeError("Could not start TimescaleDB; check Docker Desktop or set DATABASE_URL.")
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if database_ready():
            return
        time.sleep(0.5)
    raise RuntimeError("TimescaleDB did not become ready; inspect docker compose logs.")
