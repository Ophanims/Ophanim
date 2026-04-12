from datetime import datetime, timezone
from typing import Optional, Union
from util.const import TS
from skyfield.timelib import Time


def parse_datetime(value: Union[None, datetime, str]) -> Optional[datetime]:
    """Parse datetime value from None/datetime/ISO-8601 string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError(f"Unsupported datetime value: {type(value)}")


def ensure_utc(dt: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string; keep None as None."""
    if dt is None:
        return None
    return dt.isoformat()


def to_skyfield_time(dt: datetime) -> Time:
    return TS.from_datetime(ensure_utc(dt))

def skyfield_to_datetime(t: Time) -> datetime:
    return t.utc_datetime().replace(tzinfo=timezone.utc)