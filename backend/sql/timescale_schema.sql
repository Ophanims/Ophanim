-- Timescale schema for simulation records and time-series points.
-- Execute with:
--   psql "$DATABASE_URL" -f backend/sql/timescale_schema.sql

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS simulation_records (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    run_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_sim_records_project_started
    ON simulation_records (project_id, started_at DESC);

CREATE TABLE IF NOT EXISTS simulation_state_points (
    ts TIMESTAMPTZ NOT NULL,
    record_id BIGINT NOT NULL REFERENCES simulation_records(id) ON DELETE CASCADE,
    project_id BIGINT NOT NULL,
    slot_count INTEGER NOT NULL,
    timeslot DOUBLE PRECISION NOT NULL,
    now_iso TEXT,
    maximum_slot INTEGER,
    status TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (record_id, ts, slot_count)
);

SELECT create_hypertable(
    'simulation_state_points',
    by_range('ts'),
    if_not_exists => TRUE,
    migrate_data => TRUE
);

CREATE INDEX IF NOT EXISTS idx_state_points_record_ts
    ON simulation_state_points (record_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_state_points_project_ts
    ON simulation_state_points (project_id, ts DESC);

CREATE TABLE IF NOT EXISTS simulation_entity_points (
    ts TIMESTAMPTZ NOT NULL,
    record_id BIGINT NOT NULL REFERENCES simulation_records(id) ON DELETE CASCADE,
    project_id BIGINT NOT NULL,
    slot_count INTEGER NOT NULL,
    entity_id TEXT NOT NULL,
    entity_type TEXT,
    payload JSONB NOT NULL,
    PRIMARY KEY (record_id, ts, slot_count, entity_id)
);

SELECT create_hypertable(
    'simulation_entity_points',
    by_range('ts'),
    if_not_exists => TRUE,
    migrate_data => TRUE
);

CREATE INDEX IF NOT EXISTS idx_entity_points_record_ts
    ON simulation_entity_points (record_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_entity_points_project_entity_ts
    ON simulation_entity_points (project_id, entity_id, ts DESC);

-- Optional retention and compression policies (uncomment as needed).
-- ALTER TABLE simulation_state_points SET (
--     timescaledb.compress,
--     timescaledb.compress_orderby = 'ts DESC',
--     timescaledb.compress_segmentby = 'record_id'
-- );
-- SELECT add_compression_policy('simulation_state_points', INTERVAL '7 days');
-- SELECT add_retention_policy('simulation_state_points', INTERVAL '90 days');
--
-- ALTER TABLE simulation_entity_points SET (
--     timescaledb.compress,
--     timescaledb.compress_orderby = 'ts DESC',
--     timescaledb.compress_segmentby = 'record_id,entity_id'
-- );
-- SELECT add_compression_policy('simulation_entity_points', INTERVAL '7 days');
-- SELECT add_retention_policy('simulation_entity_points', INTERVAL '90 days');
