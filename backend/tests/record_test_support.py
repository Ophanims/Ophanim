"""A test double for transport tests; SQL is exercised separately against TimescaleDB."""
from simulator.services.record_contracts import RecordWindow


class MemoryRecordRepository:
    def __init__(self):
        self.records = {}
        self.frames = {}

    def ensure_schema(self):
        return None

    def create_record(self, record):
        self.records[record.record_id] = record
        self.frames[record.record_id] = []

    def get_record(self, record_id):
        if record_id not in self.records:
            raise FileNotFoundError(record_id)
        return self.records[record_id]

    def list_records(self, limit=50, project_id=None):
        return [record for record in self.records.values() if project_id is None or record.project_id == project_id][:limit]

    def append_frames(self, record_id, states):
        existing = self.frames[record_id]
        known = {(state.frame_counter, state.time) for state in existing}
        existing.extend(state for state in states if (state.frame_counter, state.time) not in known)
        self.records[record_id] = self.records[record_id].model_copy(update={"frame_count": len(existing)})

    def close_record(self, record_id, status):
        self.records[record_id] = self.records[record_id].model_copy(update={"status": status})

    def get_record_window(self, record_id, start_frame, frame_limit):
        record = self.get_record(record_id)
        frames = self.frames[record_id]
        return RecordWindow(record=record, frames=tuple(frames[start_frame:start_frame + frame_limit]),
                            start_frame=start_frame, has_more=len(frames) > start_frame + frame_limit)

    def iter_record_lines(self, record_id):
        for state in self.frames[record_id]:
            yield state.model_dump_json() + "\n"

    def delete_record(self, record_id):
        self.get_record(record_id)
        del self.records[record_id]
        del self.frames[record_id]
