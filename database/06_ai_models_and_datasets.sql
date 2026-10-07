-- 06_ai_models_and_datasets.sql
-- AI registry tables: training datasets, AI models, and which model used which dataset.
-- NOTE: the sample rows are PLACEHOLDERS. No model has been trained and no dataset
-- has been generated yet. They are updated when the ML work is done.
-- Safe to re-run only while no later table references ai_model (use ALTER after that).

DROP TABLE IF EXISTS model_training;
DROP TABLE IF EXISTS ai_model;
DROP TABLE IF EXISTS training_dataset;

-- A dataset used to train models
CREATE TABLE training_dataset (
    dataset_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name    VARCHAR(100) NOT NULL,
    version         VARCHAR(20)  NOT NULL,
    data_source_id  INT NOT NULL REFERENCES data_source(data_source_id),
    is_synthetic    BOOLEAN NOT NULL DEFAULT TRUE,
    row_count       INT CHECK (row_count >= 0),
    file_path       VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes           TEXT,
    UNIQUE (dataset_name, version)
);

-- An AI model (one row per model version)
CREATE TABLE ai_model (
    model_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name     VARCHAR(100) NOT NULL,
    version        VARCHAR(20)  NOT NULL,
    task_type      VARCHAR(30)  NOT NULL
                   CHECK (task_type IN ('RISK_CLASSIFICATION', 'ANOMALY_DETECTION', 'DEGRADATION_REGRESSION')),
    algorithm      VARCHAR(50)  NOT NULL,
    trained_at     TIMESTAMPTZ,
    artifact_path  VARCHAR(255),
    is_active      BOOLEAN NOT NULL DEFAULT FALSE,
    notes          TEXT,
    UNIQUE (model_name, version)
);

-- Many-to-many: a model can use several datasets, a dataset can feed several models
CREATE TABLE model_training (
    model_id    INT NOT NULL REFERENCES ai_model(model_id),
    dataset_id  INT NOT NULL REFERENCES training_dataset(dataset_id),
    rows_used   INT CHECK (rows_used >= 0),
    PRIMARY KEY (model_id, dataset_id)
);

-- PLACEHOLDER sample rows
INSERT INTO training_dataset (dataset_name, version, data_source_id, is_synthetic, notes)
SELECT 'synthetic_battery', 'v1', data_source_id, TRUE, 'Placeholder: dataset not generated yet'
FROM data_source WHERE source_name = 'Synthetic data generator';

INSERT INTO ai_model (model_name, version, task_type, algorithm, notes) VALUES
    ('thermal_risk_classifier', 'v0', 'RISK_CLASSIFICATION', 'RandomForestClassifier', 'Placeholder: not trained yet'),
    ('health_risk_classifier',  'v0', 'RISK_CLASSIFICATION', 'RandomForestClassifier', 'Placeholder: not trained yet'),
    ('sensor_anomaly_detector', 'v0', 'ANOMALY_DETECTION',   'IsolationForest',        'Placeholder: not trained yet');

INSERT INTO model_training (model_id, dataset_id)
SELECT m.model_id, d.dataset_id
FROM ai_model m
CROSS JOIN training_dataset d
WHERE d.dataset_name = 'synthetic_battery' AND d.version = 'v1';
