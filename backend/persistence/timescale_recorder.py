import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

import psycopg


class TimescaleRecorder:
    """Persist simulation record/state/entity points into TimescaleDB."""

    def __init__(self, dsn: Optional[str] = None):
        self.DATABASE_URL = dsn or os.getenv("DATABASE_URL")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required for TimescaleRecorder")

    def _connect(self):
        return psycopg.connect(self.DATABASE_URL)

    async def ensure_schema(self, schema_sql: str) -> None:
        await asyncio.to_thread(self._ensure_schema_sync, schema_sql)

    def _ensure_schema_sync(self, schema_sql: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
