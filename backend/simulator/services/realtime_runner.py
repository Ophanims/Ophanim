"""Advance a session independently of display cadence; record every step."""
import asyncio
import logging
from time import monotonic

from simulator.settings import SIMULATION_PUSH_INTERVAL_S

logger = logging.getLogger(__name__)


class RealtimeRunner:
    def __init__(self, session, record):
        self.session = session
        self.record = record
        self.playing = asyncio.Event()
        self.changed = asyncio.Event()
        self.stopping = False
        self.completed = False
        self.error = None
        self.latest_state = session.snapshot()
        self.task = asyncio.create_task(self._run())

    def play(self) -> None:
        if self.completed or self.error is not None:
            raise ValueError("Initialize an active session before play")
        self.playing.set()

    def pause(self) -> None:
        self.playing.clear()

    async def stop(self) -> None:
        self.stopping = True
        self.playing.set()
        # Never cancel an in-flight to_thread call: its physics objects must
        # remain alive until the step and its record append finish.
        await self.task

    def _advance(self):
        state = self.session.step()
        self.record.append_state(state)
        return state

    async def _run(self) -> None:
        last_push = 0.0
        try:
            while True:
                await self.playing.wait()
                if self.stopping:
                    return
                self.latest_state = await asyncio.to_thread(self._advance)
                if self.session.is_completed:
                    await asyncio.to_thread(self.record.close, "completed")
                    self.completed = True
                    self.changed.set()
                    return
                if monotonic() - last_push >= SIMULATION_PUSH_INTERVAL_S:
                    self.changed.set()
                    last_push = monotonic()
        except Exception as error:
            self.error = error
            logger.exception("Realtime simulation failed", extra={"record_id": self.record.record_id})
            self.changed.set()
