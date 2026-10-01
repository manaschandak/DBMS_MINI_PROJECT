-- Step 19: Index experiment (EXPLAIN ANALYZE before and after)
-- Runs on a throwaway table, temperature_reading_perf, with 200,000 SYNTHETIC readings.
-- Your real tables are not touched. The throwaway table is dropped at the end.
-- Run with:  psql -U postgres -d battery_db -f database/14_index_experiment.sql -o database/index_experiment_output.txt

\set ON_ERROR_STOP on
SET client_min_messages = warning;

DROP TABLE IF EXISTS temperature_reading_perf;

-- Same columns as temperature_reading, but deliberately WITHOUT any key or index
CREATE TABLE temperature_reading_perf (
    sensor_id       INTEGER      NOT NULL,
    recorded_at     TIMESTAMPTZ  NOT NULL,
    temperature_c   NUMERIC(5,2) NOT NULL,
    data_source_id  INTEGER
);

-- 50 sensors x 4000 readings (one per minute) = 200,000 rows.
-- About 0.1% of readings get a +25 C spike so that "high temperature" is a rare event.
INSERT INTO temperature_reading_perf (sensor_id, recorded_at, temperature_c, data_source_id)
SELECT s,
       timestamptz '2026-09-01 00:00:00+05:30' + n * interval '1 minute',
       round((25 + random() * 10 + CASE WHEN random() < 0.001 THEN 25 ELSE 0 END)::numeric, 2),
       1
FROM generate_series(1, 50) AS s,
     generate_series(0, 3999) AS n;

ANALYZE temperature_reading_perf;

\qecho ===== Rows loaded =====
SELECT count(*) AS rows_loaded FROM temperature_reading_perf;

\qecho
\qecho ===== BEFORE INDEXES - Query 1: one sensor, one day =====
EXPLAIN ANALYZE
SELECT count(*), avg(temperature_c)
FROM temperature_reading_perf
WHERE sensor_id = 7
  AND recorded_at >= timestamptz '2026-09-02 00:00:00+05:30'
  AND recorded_at <  timestamptz '2026-09-03 00:00:00+05:30';

\qecho
\qecho ===== BEFORE INDEXES - Query 2: 20 hottest readings above 50 C =====
EXPLAIN ANALYZE
SELECT sensor_id, recorded_at, temperature_c
FROM temperature_reading_perf
WHERE temperature_c > 50
ORDER BY temperature_c DESC
LIMIT 20;

-- Add the indexes
CREATE INDEX idx_perf_sensor_time ON temperature_reading_perf (sensor_id, recorded_at);
CREATE INDEX idx_perf_temp        ON temperature_reading_perf (temperature_c);

ANALYZE temperature_reading_perf;

\qecho
\qecho ===== AFTER INDEXES - Query 1: one sensor, one day =====
EXPLAIN ANALYZE
SELECT count(*), avg(temperature_c)
FROM temperature_reading_perf
WHERE sensor_id = 7
  AND recorded_at >= timestamptz '2026-09-02 00:00:00+05:30'
  AND recorded_at <  timestamptz '2026-09-03 00:00:00+05:30';

\qecho
\qecho ===== AFTER INDEXES - Query 2: 20 hottest readings above 50 C =====
EXPLAIN ANALYZE
SELECT sensor_id, recorded_at, temperature_c
FROM temperature_reading_perf
WHERE temperature_c > 50
ORDER BY temperature_c DESC
LIMIT 20;

\qecho
\qecho ===== Cost of the indexes: disk space =====
SELECT pg_size_pretty(pg_relation_size('temperature_reading_perf')) AS table_size,
       pg_size_pretty(pg_relation_size('idx_perf_sensor_time'))     AS sensor_time_index,
       pg_size_pretty(pg_relation_size('idx_perf_temp'))            AS temp_index;

-- Clean up so the database goes back to exactly 23 tables
DROP TABLE temperature_reading_perf;
