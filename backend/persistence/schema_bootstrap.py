"""Initialize retained databases before importing their historical data."""
from pathlib import Path
from persistence.legacy_mysql_schema import ensure_projects_table
from persistence.timescale_recorder import TimescaleRecorder


async def ensure_record_schema():
    recorder = TimescaleRecorder()
    directory = Path(__file__).resolve().parents[1] / "sql"
    await recorder.ensure_schema((directory / "timescale_schema.sql").read_text())
    backfill = directory / "backfill_slot_count.sql"
    if backfill.exists():
        await recorder.ensure_schema(backfill.read_text())
