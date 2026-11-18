"""Idempotently import existing NDJSON records or recovery journals into TimescaleDB."""
import argparse
import sys

from run_backend import ROOT, load_environment

load_environment()
sys.path.insert(0, str(ROOT / "backend"))
from persistence.record_repository import RecordRepository
from simulator.services.record_import import import_record_files
from simulator.settings import SIMULATION_DATA_DIR


if __name__ == "__main__":
    load_environment()
    from record_database import configure_record_database
    configure_record_database()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery", action="store_true", help="Import record_recovery/ instead of old records/")
    arguments = parser.parse_args()
    repository = RecordRepository()
    repository.ensure_schema()
    directory = SIMULATION_DATA_DIR / ("record_recovery" if arguments.recovery else "records")
    print(f"Imported {import_record_files(directory, repository)} records; source files retained.")
