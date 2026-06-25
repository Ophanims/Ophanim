-- Backfill slot_count for records that were recorded before the nesting fix.
-- The old code stored slot_count at state["clock"]["slot_count"], but the
-- recorder read from the top level — which didn't exist — so all rows got 0.
--
-- Run once after deploying the fix, or automatically on next startup:
--   psql "$DATABASE_URL" -f backend/sql/backfill_slot_count.sql

-- 1. Fix state_points: extract slot_count from payload->'clock'->>'slot_count'
UPDATE simulation_state_points
SET slot_count = (payload #>> '{clock,slot_count}')::int
WHERE slot_count = 0
  AND payload #>> '{clock,slot_count}' IS NOT NULL;

-- 2. Fix entity_points: copy the corrected slot_count from the matching
--    state_point (same record_id + ts, inserted in the same transaction).
UPDATE simulation_entity_points ep
SET slot_count = sp.slot_count
FROM simulation_state_points sp
WHERE ep.record_id = sp.record_id
  AND ep.ts = sp.ts
  AND ep.slot_count = 0
  AND sp.slot_count > 0;
