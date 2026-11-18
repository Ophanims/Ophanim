"""Recording failure, final flush and control responsiveness regressions."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from simulator.core.session import SimulationSession
from simulator.defaults import default_project
from simulator.services.project_service import detect_update
from simulator.services.realtime_runner import RealtimeRunner
from simulator.services.session_records import SessionRecord
from simulator.services.record_import import import_record_files
from record_test_support import MemoryRecordRepository


class RecordWriterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.repository = MemoryRecordRepository()
        for target, value in (("simulator.services.session_records.RecordRepository", lambda: self.repository),
                              ("simulator.services.session_records.SIMULATION_RECOVERY_DIR", self.root)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.project = detect_update(default_project())
        self.session = SimulationSession(self.project)
        self.addCleanup(self.session.close)

    def test_close_flushes_partial_batch_and_is_idempotent(self):
        record = SessionRecord(self.project, "geometry")
        states = [self.session.snapshot(), self.session.step()]
        for state in states:
            record.append_state(state)
        record.close("completed")
        record.close("disconnected")
        self.assertEqual(states, self.repository.frames[record.record_id])
        self.assertEqual("completed", self.repository.get_record(record.record_id).status)
        self.assertEqual([], list(self.root.iterdir()))

    def test_failed_batch_retains_recoverable_snapshot_and_metadata(self):
        record = SessionRecord(self.project, "geometry")
        state = self.session.snapshot()
        with patch.object(self.repository, "append_frames", side_effect=RuntimeError("database unavailable")):
            record.append_state(state)
            with self.assertLogs("simulator.services.record_writer", level="ERROR"):
                with self.assertRaisesRegex(RuntimeError, "recovery journal retained"):
                    record.close("completed")
        self.assertEqual(state.model_dump_json() + "\n", (self.root / f"{record.record_id}.ndjson").read_text())
        self.assertIn('"status":"failed"', (self.root / f"{record.record_id}.json").read_text())
        self.assertEqual(0, self.repository.get_record(record.record_id).frame_count)
        self.assertEqual("failed", self.repository.get_record(record.record_id).status)
        self.assertEqual(1, import_record_files(self.root, self.repository))
        self.assertEqual(1, import_record_files(self.root, self.repository))
        self.assertEqual(1, self.repository.get_record(record.record_id).frame_count)
        self.assertEqual(state, self.repository.frames[record.record_id][0])


class RealtimeRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_steps_and_final_flush_do_not_wait_for_a_display_consumer(self):
        class Session:
            counter = 0
            is_completed = False

            def snapshot(self):
                return self.counter

            def step(self):
                self.counter += 1
                self.is_completed = self.counter == 100
                return self.counter

        class Record:
            record_id = "test"

            def __init__(self):
                self.states = []
                self.status = "running"

            def append_state(self, state):
                self.states.append(state)

            def close(self, status):
                self.status = status

        record = Record()
        runner = RealtimeRunner(Session(), record)
        runner.play()
        try:
            await asyncio.wait_for(asyncio.shield(runner.task), 3)
            self.assertEqual(list(range(1, 101)), record.states)
            self.assertEqual(100, runner.latest_state)
            self.assertEqual("completed", record.status)
            self.assertTrue(runner.completed)
        finally:
            await runner.stop()

    async def test_pause_and_stop_do_not_destroy_an_inflight_step(self):
        started, release = Event(), Event()
        state = type("State", (), {"frame_counter": 1})()

        class Session:
            is_completed = False

            def snapshot(self):
                return state

            def step(self):
                started.set()
                release.wait(5)
                return state

        class Record:
            record_id = "test"
            states = []

            def append_state(self, state):
                self.states.append(state)

        record = Record()
        runner = RealtimeRunner(Session(), record)
        runner.play()
        try:
            self.assertTrue(await asyncio.to_thread(started.wait, 2))
            runner.pause()
            stopping = asyncio.create_task(runner.stop())
            await asyncio.sleep(0)
            self.assertFalse(stopping.done())
            release.set()
            await asyncio.wait_for(stopping, 2)
            self.assertEqual([state], record.states)
        finally:
            release.set()
            await runner.stop()
