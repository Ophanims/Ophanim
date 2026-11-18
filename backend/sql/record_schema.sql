-- Canonical simulation records and analysis tables in the ophanim schema.
CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;

CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    project JSONB NOT NULL,
    code_hash TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    status TEXT NOT NULL,
    frame_count BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS records_project_created ON records (project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS simulation_frames (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time)
);
SELECT create_hypertable('simulation_frames', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS satellite_states (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    id TEXT NOT NULL,
    battery_percent DOUBLE PRECISION NOT NULL,
    task_queue INTEGER NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time, id)
);
SELECT create_hypertable('satellite_states', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS satellite_states_entity ON satellite_states (record_id, id, frame_counter, time);

CREATE TABLE IF NOT EXISTS station_states (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    id TEXT NOT NULL,
    on_upload BOOLEAN NOT NULL,
    on_download BOOLEAN NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time, id)
);
SELECT create_hypertable('station_states', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS station_states_entity ON station_states (record_id, id, frame_counter, time);

CREATE TABLE IF NOT EXISTS task_states (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    id TEXT NOT NULL,
    is_done BOOLEAN NOT NULL,
    workload_percent DOUBLE PRECISION NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time, id)
);
SELECT create_hypertable('task_states', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS task_states_entity ON task_states (record_id, id, frame_counter, time);

CREATE TABLE IF NOT EXISTS mission_states (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    id TEXT NOT NULL,
    status TEXT NOT NULL,
    position TEXT NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time, id)
);
SELECT create_hypertable('mission_states', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS mission_states_entity ON mission_states (record_id, id, frame_counter, time);

CREATE TABLE IF NOT EXISTS link_states (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    type TEXT NOT NULL,
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    distance DOUBLE PRECISION NOT NULL,
    snr DOUBLE PRECISION NOT NULL,
    rate DOUBLE PRECISION NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time, type, src, dst)
);
SELECT create_hypertable('link_states', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS link_states_endpoints ON link_states (record_id, src, dst, frame_counter, time);

CREATE TABLE IF NOT EXISTS network_metrics (
    time TIMESTAMPTZ NOT NULL,
    record_id TEXT NOT NULL REFERENCES records(record_id) ON DELETE CASCADE,
    frame_counter BIGINT NOT NULL,
    num_nodes INTEGER NOT NULL,
    num_edges INTEGER NOT NULL,
    num_tasks INTEGER NOT NULL,
    reward DOUBLE PRECISION NOT NULL,
    average_battery_percent DOUBLE PRECISION NOT NULL,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, frame_counter, time)
);
SELECT create_hypertable('network_metrics', 'time', if_not_exists => TRUE);
