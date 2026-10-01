-- Step 13: Feedback (actual outcomes recorded against earlier predictions)
-- Safe to re-run: drops and recreates only the feedback table.

DROP TABLE IF EXISTS feedback CASCADE;

CREATE TABLE feedback (
    feedback_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prediction_id      INTEGER NOT NULL
                       REFERENCES prediction_result (prediction_id) ON DELETE CASCADE,
    actual_outcome     VARCHAR(10) NOT NULL
                       CHECK (actual_outcome IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    outcome_source     VARCHAR(20) NOT NULL
                       CHECK (outcome_source IN ('SERVICE_INSPECTION', 'LAB_TEST',
                                                 'FIELD_OBSERVATION', 'SIMULATION')),
    submitted_by_role  VARCHAR(20) NOT NULL
                       CHECK (submitted_by_role IN ('ADMIN', 'BMS_ENGINEER', 'FLEET_OPERATOR',
                                                    'SERVICE_TECHNICIAN', 'RESEARCHER')),
    observed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Feedback is looked up by prediction (accuracy monitoring joins on this)
CREATE INDEX idx_feedback_prediction ON feedback (prediction_id);

-- SAMPLE ROWS (fake, for testing accuracy queries before the ML exists).
-- Prediction PN-NCA-0001 / HEALTH is deliberately left without feedback,
-- so we can later test "predictions still waiting for an outcome".
INSERT INTO feedback (prediction_id, actual_outcome, outcome_source, submitted_by_role, notes)
SELECT p.prediction_id, 'LOW', 'SERVICE_INSPECTION', 'SERVICE_TECHNICIAN',
       'SAMPLE ROW: not a real outcome'
FROM prediction_result p
JOIN battery b  ON p.battery_id = b.battery_id
JOIN ai_model m ON p.model_id = m.model_id
WHERE b.serial_number = 'EC-LFP-0001' AND m.risk_type = 'THERMAL';

INSERT INTO feedback (prediction_id, actual_outcome, outcome_source, submitted_by_role, notes)
SELECT p.prediction_id, 'CRITICAL', 'SERVICE_INSPECTION', 'SERVICE_TECHNICIAN',
       'SAMPLE ROW: not a real outcome'
FROM prediction_result p
JOIN battery b  ON p.battery_id = b.battery_id
JOIN ai_model m ON p.model_id = m.model_id
WHERE b.serial_number = 'PN-NCA-0001' AND m.risk_type = 'THERMAL';

INSERT INTO feedback (prediction_id, actual_outcome, outcome_source, submitted_by_role, notes)
SELECT p.prediction_id, 'LOW', 'FIELD_OBSERVATION', 'FLEET_OPERATOR',
       'SAMPLE ROW: not a real outcome'
FROM prediction_result p
JOIN battery b  ON p.battery_id = b.battery_id
JOIN ai_model m ON p.model_id = m.model_id
WHERE b.serial_number = 'VC-NMC-0001' AND m.risk_type = 'THERMAL';
