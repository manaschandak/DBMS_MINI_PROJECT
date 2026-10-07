-- Step 20: Indexes on the real tables
-- Chosen from (a) join columns used by the dashboard views and the trigger,
-- (b) the queries the API will run, and (c) the Step 19 experiment.
-- Primary keys and unique constraints already have indexes; PostgreSQL does NOT
-- create indexes on foreign key columns automatically, so those are added here.
-- Safe to re-run: every index uses IF NOT EXISTS.

-- battery: joins to chemistry and manufacturer (v_battery_overview, v_chemistry_comparison)
CREATE INDEX IF NOT EXISTS idx_battery_chemistry    ON battery (chemistry_id);
CREATE INDEX IF NOT EXISTS idx_battery_manufacturer ON battery (manufacturer_id);

-- prediction_result: "latest prediction for a battery" (v_latest_risk) and per-model lookups
CREATE INDEX IF NOT EXISTS idx_prediction_battery_time ON prediction_result (battery_id, predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_model        ON prediction_result (model_id);

-- alert: find alerts for an assessment; partial index covering only OPEN alerts
CREATE INDEX IF NOT EXISTS idx_alert_assessment ON alert (assessment_id);
CREATE INDEX IF NOT EXISTS idx_alert_open       ON alert (alert_priority_id, created_at DESC) WHERE status = 'OPEN';

-- recommendation: by assessment, by anomaly, and "recommendations for my role, newest first"
CREATE INDEX IF NOT EXISTS idx_recommendation_assessment ON recommendation (assessment_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_anomaly    ON recommendation (anomaly_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_role_time  ON recommendation (target_role, created_at DESC);

-- sensor_anomaly: recent anomalies across the fleet
CREATE INDEX IF NOT EXISTS idx_anomaly_detected_at ON sensor_anomaly (detected_at DESC);

-- cfd_simulation: latest simulation for a digital twin
CREATE INDEX IF NOT EXISTS idx_cfd_twin_time ON cfd_simulation (twin_id, run_at DESC);

-- model_training: reverse lookup, "which models used this dataset"
CREATE INDEX IF NOT EXISTS idx_model_training_dataset ON model_training (dataset_id);

-- temperature_reading (high-frequency table, so only two indexes to keep inserts fast):
--  * temperature_c: backed by the Step 19 experiment (high-temperature search)
--  * BRIN on recorded_at: tiny index for time-range scans over append-only time-series data
CREATE INDEX IF NOT EXISTS idx_temperature_value     ON temperature_reading (temperature_c);
CREATE INDEX IF NOT EXISTS idx_temperature_time_brin ON temperature_reading USING brin (recorded_at);

ANALYZE;
