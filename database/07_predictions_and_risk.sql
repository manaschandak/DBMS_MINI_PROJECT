-- 07_predictions_and_risk.sql
-- Alert priorities, model predictions, and risk assessments.
-- Also CHANGES ai_model (adds risk_type) using ALTER.
-- NOTE: the sample predictions are SAMPLE ROWS, not produced by any trained model.
-- They exist only to test queries and will be deleted when real ML predictions exist.
-- Safe to re-run only while no later table references these tables (use ALTER after that).

-- 1) ai_model: say which kind of risk a classifier predicts
ALTER TABLE ai_model ADD COLUMN IF NOT EXISTS risk_type VARCHAR(10)
    CHECK (risk_type IN ('THERMAL', 'HEALTH'));
UPDATE ai_model SET risk_type = 'THERMAL' WHERE model_name = 'thermal_risk_classifier';
UPDATE ai_model SET risk_type = 'HEALTH'  WHERE model_name = 'health_risk_classifier';
ALTER TABLE ai_model DROP CONSTRAINT IF EXISTS chk_classifier_has_risk_type;
ALTER TABLE ai_model ADD CONSTRAINT chk_classifier_has_risk_type
    CHECK (task_type <> 'RISK_CLASSIFICATION' OR risk_type IS NOT NULL);

-- 2) New tables (drop only these three)
DROP TABLE IF EXISTS risk_assessment;
DROP TABLE IF EXISTS prediction_result;
DROP TABLE IF EXISTS alert_priority;

-- How urgent an alert is (lookup table)
CREATE TABLE alert_priority (
    alert_priority_id  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    priority_code      VARCHAR(10) NOT NULL UNIQUE,
    severity_level     INT NOT NULL UNIQUE CHECK (severity_level BETWEEN 1 AND 4),
    description        TEXT
);

-- Raw output of an AI model for one battery
CREATE TABLE prediction_result (
    prediction_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id         INT NOT NULL REFERENCES ai_model(model_id),
    battery_id       INT NOT NULL REFERENCES battery(battery_id),
    predicted_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    predicted_label  VARCHAR(10) NOT NULL
                     CHECK (predicted_label IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    confidence       NUMERIC(4,3) CHECK (confidence BETWEEN 0 AND 1),
    notes            TEXT
);

-- Final risk decision for a prediction: the model's label, optionally escalated by safety rules
CREATE TABLE risk_assessment (
    assessment_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prediction_id     INT NOT NULL UNIQUE REFERENCES prediction_result(prediction_id),
    final_risk_level  VARCHAR(10) NOT NULL
                      CHECK (final_risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    rule_override     BOOLEAN NOT NULL DEFAULT FALSE,
    assessed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3) Sample data
INSERT INTO alert_priority (priority_code, severity_level, description) VALUES
    ('LOW',      1, 'Informational, no action needed'),
    ('MEDIUM',   2, 'Review at next scheduled check'),
    ('HIGH',     3, 'Inspect soon'),
    ('CRITICAL', 4, 'Immediate action required');

-- SAMPLE predictions (not from a trained model)
INSERT INTO prediction_result (model_id, battery_id, predicted_label, confidence, notes)
SELECT m.model_id, b.battery_id, v.label, v.conf, 'SAMPLE ROW: not produced by a trained model'
FROM (VALUES
    ('VC-NMC-0001', 'thermal_risk_classifier', 'MEDIUM', 0.700),
    ('EC-LFP-0001', 'thermal_risk_classifier', 'LOW',    0.900),
    ('PN-NCA-0001', 'thermal_risk_classifier', 'HIGH',   0.800),
    ('PN-NCA-0001', 'health_risk_classifier',  'MEDIUM', 0.650)
) AS v(serial, model_name, label, conf)
JOIN battery b  ON b.serial_number = v.serial
JOIN ai_model m ON m.model_name = v.model_name AND m.version = 'v0';

-- SAMPLE risk assessments (one per prediction; one is escalated by a safety rule)
INSERT INTO risk_assessment (prediction_id, final_risk_level, rule_override)
SELECT p.prediction_id, v.final_level, v.override
FROM (VALUES
    ('VC-NMC-0001', 'thermal_risk_classifier', 'MEDIUM',   FALSE),
    ('EC-LFP-0001', 'thermal_risk_classifier', 'LOW',      FALSE),
    ('PN-NCA-0001', 'thermal_risk_classifier', 'CRITICAL', TRUE),
    ('PN-NCA-0001', 'health_risk_classifier',  'MEDIUM',   FALSE)
) AS v(serial, model_name, final_level, override)
JOIN battery b            ON b.serial_number = v.serial
JOIN ai_model m           ON m.model_name = v.model_name AND m.version = 'v0'
JOIN prediction_result p  ON p.battery_id = b.battery_id AND p.model_id = m.model_id;
