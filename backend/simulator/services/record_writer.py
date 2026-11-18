"""Bounded background batches; completion means all accepted frames committed."""
import logging
from queue import Empty, Full, Queue
from threading import Thread
from time import monotonic

logger = logging.getLogger(__name__)


class RecordWriter:
    def __init__(self, repository, record_id: str, batch_size: int = 16, flush_interval: float = 0.1):
        self.repository = repository
        self.record_id = record_id
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue(maxsize=32)
        self.error = None
        self.thread = Thread(target=self._run, name=f"record-{record_id}", daemon=True)
        self.thread.start()

    def check(self) -> None:
        if self.error is not None:
            raise RuntimeError("TimescaleDB record write failed; recovery journal retained") from self.error

    def append(self, state) -> None:
        self._put(state)

    def _put(self, value) -> None:
        while True:
            self.check()
            try:
                self.queue.put(value, timeout=0.1)
                self.check()
                return
            except Full:
                continue

    def finish(self) -> None:
        try:
            self._put(None)
        finally:
            self.thread.join()
        self.check()

    def _run(self) -> None:
        try:
            batch = []
            deadline = monotonic() + self.flush_interval
            while True:
                try:
                    state = self.queue.get(timeout=max(0, deadline - monotonic()))
                except Empty:
                    state = False
                if state is not False and state is not None:
                    batch.append(state)
                if batch and (state is None or len(batch) >= self.batch_size or monotonic() >= deadline):
                    self.repository.append_frames(self.record_id, batch)
                    batch = []
                    deadline = monotonic() + self.flush_interval
                elif monotonic() >= deadline:
                    deadline = monotonic() + self.flush_interval
                if state is None:
                    return
        except Exception as error:
            self.error = error
            logger.exception("Record batch failed", extra={"record_id": self.record_id})
