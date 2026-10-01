-- Step 14: Model Performance + live accuracy view
-- Safe to re-run: drops and recreates only the view and model_performance.

DROP VIEW IF EXISTS v_live_accuracy;
DROP TABLE IF EXISTS model_performance CASCADE;

CREATE TABLE model_performance (
    performance_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id              INTEGER NOT NULL
                          REFERENCES ai_model (model_id) ON DELETE CASCADE,
    evaluation_type       VARCHAR(15) NOT NULL
                          CHECK (evaluation_type IN ('TEST_SET', 'LIVE_FEEDBACK')),
    sample_count          INTEGER NOT NULL CHECK (sample_count > 0),
    accuracy              NUMERIC(4,3) CHECK (accuracy BETWEEN 0 AND 1),
    macro_f1              NUMERIC(4,3) CHECK (macro_f1 BETWEEN 0 AND 1),
    recall_high_critical  NUMERIC(4,3) CHECK (recall_high_critical BETWEEN 0 AND 1),
    evaluated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes                 TEXT
);

CREATE INDEX idx_model_performance_model ON model_performance (model_id, evaluated_at);

-- View: accuracy of each classifier measured against recorded feedback.
-- Not stored anywhere: it is worked out from prediction_result + feedback.
-- Compares the model's raw predicted_label with the actual outcome.
-- "underestimated" = the real outcome was MORE severe than predicted (the dangerous mistake).
CREATE VIEW v_live_accuracy AS
SELECT
    m.model_id,
    m.model_name,
    m.risk_type,
    count(*) AS feedback_count,
    count(*) FILTER (WHERE p.predicted_label = f.actual_outcome) AS exact_matches,
    round(
        count(*) FILTER (WHERE p.predicted_label = f.actual_outcome)::numeric / count(*), 3
    ) AS accuracy,
    count(*) FILTER (
        WHERE array_position(ARRAY['LOW','MEDIUM','HIGH','CRITICAL'], f.actual_outcome::text)
            > array_position(ARRAY['LOW','MEDIUM','HIGH','CRITICAL'], p.predicted_label::text)
    ) AS underestimated
FROM feedback f
JOIN prediction_result p ON f.prediction_id = p.prediction_id
JOIN ai_model m          ON p.model_id = m.model_id
GROUP BY m.model_id, m.model_name, m.risk_type;

-- SAMPLE ROWS (fake, for testing before real evaluation exists)
INSERT INTO model_performance
    (model_id, evaluation_type, sample_count, accuracy, macro_f1, recall_high_critical, notes)
SELECT model_id, 'TEST_SET', 1000, 0.900, 0.880, 0.950,
       'SAMPLE ROW: not from a real evaluation'
FROM ai_model WHERE model_name = 'thermal_risk_classifier';

INSERT INTO model_performance
    (model_id, evaluation_type, sample_count, accuracy, macro_f1, recall_high_critical, notes)
SELECT model_id, 'TEST_SET', 1000, 0.850, 0.830, 0.900,
       'SAMPLE ROW: not from a real evaluation'
FROM ai_model WHERE model_name = 'health_risk_classifier';
