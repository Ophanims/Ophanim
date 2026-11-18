"""Run record integration tests in disposable schemas on the configured TimescaleDB."""
import os
import sys
import unittest

from run_backend import ROOT, load_environment
from record_database import configure_record_database

if __name__ == "__main__":
    load_environment()
    configure_record_database()
    os.environ["TEST_DATABASE_URL"] = os.environ["DATABASE_URL"]
    sys.path.insert(0, str(ROOT / "backend"))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "backend" / "tests"), pattern="test_timescale_records.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
