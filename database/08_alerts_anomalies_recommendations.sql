-- 08_alerts_anomalies_recommendations.sql
-- Sensor anomalies, alerts (early warnings) and recommendations.
-- NOTE: all sample rows are SAMPLE ROWS, not real detections or model output.
-- Safe to re-run only while no later table references these tables (use ALTER after that).

DROP TABLE IF EXISTS recommendation;
DROP TABLE IF EXISTS alert;
DROP TABLE IF EXISTS sensor_anomaly;

-- An unusual reading found on a sensor (by a rule or by the ML model)
CREATE TABLE sensor_anomaly (
    anomaly_id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id         INT NOT NULL REFERENCES sensor(sensor_id),
    detected_at       TIMESTAMPTZ NOT NULL,
    anomaly_type      VARCHAR(20) NOT NULL
                      CHECK (anomaly_type IN ('OUT_OF_RANGE', 'SUDDEN_SPIKE', 'FLATLINE', 'DRIFT', 'MODEL_OUTLIER')),
    cause             VARCHAR(15) NOT NULL DEFAULT 'UNDETERMINED'
                      CHECK (cause IN ('SENSOR_FAULT', 'BATTERY_ISSUE', 'UNDETERMINED')),
    detection_method  VARCHAR(10) NOT NULL
                      CHECK (detection_method IN ('RULE', 'ML_MODEL')),
    model_id          INT REFERENCES ai_model(model_id),
    anomaly_score     NUMERIC(6,3),
    details           TEXT,
    UNIQUE (sensor_id, detected_at, anomaly_type),
    CONSTRAINT chk_anomaly_method_matches_model
        CHECK ((detection_method = 'ML_MODEL') = (model_id IS NOT NULL))
);

-- An early warning raised from a risk assessment
CREATE TABLE alert (
    alert_id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    assessment_id      INT NOT NULL REFERENCES risk_assessment(assessment_id),
    alert_priority_id  INT NOT NULL REFERENCES alert_priority(alert_priority_id),
    message            TEXT NOT NULL,
    status             VARCHAR(15) NOT NULL DEFAULT 'OPEN'
                       CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at    TIMESTAMPTZ,
    CONSTRAINT chk_alert_ack_matches_status
        CHECK ((status = 'OPEN' AND acknowledged_at IS NULL)
            OR (status <> 'OPEN' AND acknowledged_at IS NOT NULL))
);

-- Advice for a role, generated from EITHER a risk assessment OR a sensor anomaly
CREATE TABLE recommendation (
    recommendation_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_role          VARCHAR(20) NOT NULL
                         CHECK (target_role IN ('BMS_ENGINEER', 'FLEET_OPERATOR', 'MANUFACTURER', 'SERVICE_TECHNICIAN')),
    assessment_id        INT REFERENCES risk_assessment(assessment_id),
    anomaly_id           INT REFERENCES sensor_anomaly(anomaly_id),
    recommendation_text  TEXT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_recommendation_one_source
        CHECK (num_nonnulls(assessment_id, anomaly_id) = 1)
);

-- SAMPLE anomalies (not real detections)
INSERT INTO sensor_anomaly (sensor_id, detected_at, anomaly_type, cause, detection_method, model_id, anomaly_score, details)
SELECT s.sensor_id, '2026-10-01 09:02:00+05:30'::timestamptz, v.atype, v.cause, v.method, m.model_id, v.score, v.details
FROM (VALUES
    ('VC-NMC-0001', 'CELL_2',   'SUDDEN_SPIKE',  'SENSOR_FAULT', 'RULE',     NULL::text,                 NULL::numeric, 'SAMPLE ROW: not a real detection'),
    ('EC-LFP-0001', 'BMS_MAIN', 'MODEL_OUTLIER', 'UNDETERMINED', 'ML_MODEL', 'sensor_anomaly_detector',  0.620,         'SAMPLE ROW: not a real detection')
) AS v(serial, location, atype, cause, method, model_name, score, details)
JOIN battery b     ON b.serial_number = v.serial
JOIN sensor s      ON s.battery_id = b.battery_id AND s.location = v.location
LEFT JOIN ai_model m ON m.model_name = v.model_name AND m.version = 'v0';

-- SAMPLE alerts (not real warnings)
INSERT INTO alert (assessment_id, alert_priority_id, message, status, acknowledged_at)
SELECT r.assessment_id, ap.alert_priority_id, v.msg, v.status, v.ack::timestamptz
FROM (VALUES
    ('PN-NCA-0001', 'thermal_risk_classifier', 'CRITICAL', 'SAMPLE: critical thermal risk on PN-NCA-0001', 'OPEN',         NULL::text),
    ('VC-NMC-0001', 'thermal_risk_classifier', 'MEDIUM',   'SAMPLE: medium thermal risk on VC-NMC-0001',   'ACKNOWLEDGED', '2026-10-01 09:30:00+05:30')
) AS v(serial, model_name, priority, msg, status, ack)
JOIN battery b            ON b.serial_number = v.serial
JOIN ai_model m           ON m.model_name = v.model_name AND m.version = 'v0'
JOIN prediction_result p  ON p.battery_id = b.battery_id AND p.model_id = m.model_id
JOIN risk_assessment r    ON r.prediction_id = p.prediction_id
JOIN alert_priority ap    ON ap.priority_code = v.priority;

-- SAMPLE recommendations from a risk assessment
INSERT INTO recommendation (target_role, assessment_id, recommendation_text)
SELECT v.role, r.assessment_id, v.txt
FROM (VALUES
    ('PN-NCA-0001', 'thermal_risk_classifier', 'SERVICE_TECHNICIAN', 'SAMPLE: Inspect this battery and its coolant loop immediately.'),
    ('PN-NCA-0001', 'thermal_risk_classifier', 'FLEET_OPERATOR',     'SAMPLE: Take the vehicle out of service until it has been inspected.')
) AS v(serial, model_name, role, txt)
JOIN battery b            ON b.serial_number = v.serial
JOIN ai_model m           ON m.model_name = v.model_name AND m.version = 'v0'
JOIN prediction_result p  ON p.battery_id = b.battery_id AND p.model_id = m.model_id
JOIN risk_assessment r    ON r.prediction_id = p.prediction_id;

-- SAMPLE recommendation from a sensor anomaly
INSERT INTO recommendation (target_role, anomaly_id, recommendation_text)
SELECT 'BMS_ENGINEER', a.anomaly_id, 'SAMPLE: Check this temperature sensor; the reading may be faulty.'
FROM sensor_anomaly a
WHERE a.anomaly_type = 'SUDDEN_SPIKE';
