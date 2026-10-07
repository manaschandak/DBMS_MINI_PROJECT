-- Step 21: Transaction demo - batch ingestion of sensor readings
-- Shows atomicity (all-or-nothing), error handling inside a transaction,
-- SAVEPOINT (partial rollback) and COMMIT.
--
-- No assumptions about your sample data: the "new" readings are copies of existing
-- readings moved forward by 1 or 2 days plus 37 seconds. The 37 seconds is a marker
-- so the cleanup at the end deletes ONLY the rows this script created.
-- At the end the tables are back to their starting row counts.
--
-- Run with (see the step instructions for the exact command):
--   cmd /c "psql -U postgres -d battery_db -f database/16_transaction_demo.sql 2>&1"

\set ON_ERROR_STOP off

\echo ===== 0. Starting row counts =====
SELECT (SELECT count(*) FROM temperature_reading) AS temperature_rows,
       (SELECT count(*) FROM electrical_reading)  AS electrical_rows;

-- ---------------------------------------------------------------------------
\echo
\echo ===== 1. Batch with one bad row: the WHOLE batch must be rolled back =====
BEGIN;

INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c, data_source_id)
SELECT sensor_id, recorded_at + interval '1 day 37 seconds', temperature_c, data_source_id
FROM temperature_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 2;

INSERT INTO electrical_reading (sensor_id, recorded_at, voltage_v, current_a, data_source_id)
SELECT sensor_id, recorded_at + interval '1 day 37 seconds', voltage_v, current_a, data_source_id
FROM electrical_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 2;

\echo -- Inside the transaction the good rows are visible (4 more rows in total):
SELECT (SELECT count(*) FROM temperature_reading) AS temperature_rows,
       (SELECT count(*) FROM electrical_reading)  AS electrical_rows;

\echo -- Now a BAD row: it repeats an existing (sensor_id, recorded_at) key. Expect an ERROR:
INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c, data_source_id)
SELECT sensor_id, recorded_at, temperature_c, data_source_id
FROM temperature_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 1;

\echo -- The transaction is now aborted, so even a simple command is refused. Expect an ERROR:
SELECT 1;

ROLLBACK;

\echo -- After ROLLBACK the counts must be back to the starting numbers:
SELECT (SELECT count(*) FROM temperature_reading) AS temperature_rows,
       (SELECT count(*) FROM electrical_reading)  AS electrical_rows;

-- ---------------------------------------------------------------------------
\echo
\echo ===== 2. Same batch, but the bad row is isolated with a SAVEPOINT =====
BEGIN;

INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c, data_source_id)
SELECT sensor_id, recorded_at + interval '1 day 37 seconds', temperature_c, data_source_id
FROM temperature_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 2;

INSERT INTO electrical_reading (sensor_id, recorded_at, voltage_v, current_a, data_source_id)
SELECT sensor_id, recorded_at + interval '1 day 37 seconds', voltage_v, current_a, data_source_id
FROM electrical_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 2;

SAVEPOINT before_bad_row;

\echo -- Bad row again (duplicate key). Expect an ERROR:
INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c, data_source_id)
SELECT sensor_id, recorded_at, temperature_c, data_source_id
FROM temperature_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 1;

\echo -- Undo only the bad row; the earlier good rows stay:
ROLLBACK TO SAVEPOINT before_bad_row;

\echo -- The transaction works again, so add one more good row:
INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c, data_source_id)
SELECT sensor_id, recorded_at + interval '2 days 37 seconds', temperature_c, data_source_id
FROM temperature_reading
WHERE recorded_at < timestamptz '2026-10-02 00:00:00+05:30'
ORDER BY sensor_id, recorded_at
LIMIT 1;

COMMIT;

\echo -- After COMMIT the good rows are kept (3 temperature + 2 electrical more than the start):
SELECT (SELECT count(*) FROM temperature_reading) AS temperature_rows,
       (SELECT count(*) FROM electrical_reading)  AS electrical_rows;

-- ---------------------------------------------------------------------------
\echo
\echo ===== 3. Clean up: delete only the rows this script created =====
DELETE FROM temperature_reading
WHERE recorded_at >= timestamptz '2026-10-02 00:00:00+05:30'
  AND extract(second FROM recorded_at) = 37;

DELETE FROM electrical_reading
WHERE recorded_at >= timestamptz '2026-10-02 00:00:00+05:30'
  AND extract(second FROM recorded_at) = 37;

\echo -- Final counts, same as the start:
SELECT (SELECT count(*) FROM temperature_reading) AS temperature_rows,
       (SELECT count(*) FROM electrical_reading)  AS electrical_rows;
