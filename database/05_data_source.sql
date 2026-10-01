-- 05_data_source.sql
-- Adds the Data_Source table and tags existing data with where it came from.
-- Pattern for adding a REQUIRED column to a table that already has rows:
--   1) add the column as nullable   2) fill existing rows   3) make it NOT NULL
-- Safe to re-run.

CREATE TABLE IF NOT EXISTS data_source (
    data_source_id  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name     VARCHAR(100) NOT NULL UNIQUE,
    source_type     VARCHAR(20)  NOT NULL
                    CHECK (source_type IN ('SIMULATOR', 'CSV_UPLOAD', 'MANUAL_ENTRY',
                                           'CFD_IMPORT', 'PUBLIC_DATASET', 'SENSOR_HARDWARE')),
    description     TEXT
);

INSERT INTO data_source (source_name, source_type, description) VALUES
    ('Synthetic data generator', 'SIMULATOR',    'Python script that generates labelled synthetic data'),
    ('CSV upload',               'CSV_UPLOAD',   'Readings uploaded from a CSV file through the website'),
    ('Manual entry form',        'MANUAL_ENTRY', 'Readings typed in through the website'),
    ('CFD result import',        'CFD_IMPORT',   'Results imported from a CFD simulation run')
ON CONFLICT (source_name) DO NOTHING;

-- 1) Add the column (nullable for now)
ALTER TABLE temperature_reading ADD COLUMN IF NOT EXISTS data_source_id INT REFERENCES data_source(data_source_id);
ALTER TABLE coolant_flow        ADD COLUMN IF NOT EXISTS data_source_id INT REFERENCES data_source(data_source_id);
ALTER TABLE electrical_reading  ADD COLUMN IF NOT EXISTS data_source_id INT REFERENCES data_source(data_source_id);
ALTER TABLE aging_record        ADD COLUMN IF NOT EXISTS data_source_id INT REFERENCES data_source(data_source_id);
ALTER TABLE cfd_simulation      ADD COLUMN IF NOT EXISTS data_source_id INT REFERENCES data_source(data_source_id);

-- 2) Fill existing rows (all current sample rows are synthetic)
UPDATE temperature_reading SET data_source_id = (SELECT data_source_id FROM data_source WHERE source_name = 'Synthetic data generator') WHERE data_source_id IS NULL;
UPDATE coolant_flow        SET data_source_id = (SELECT data_source_id FROM data_source WHERE source_name = 'Synthetic data generator') WHERE data_source_id IS NULL;
UPDATE electrical_reading  SET data_source_id = (SELECT data_source_id FROM data_source WHERE source_name = 'Synthetic data generator') WHERE data_source_id IS NULL;
UPDATE aging_record        SET data_source_id = (SELECT data_source_id FROM data_source WHERE source_name = 'Synthetic data generator') WHERE data_source_id IS NULL;
UPDATE cfd_simulation      SET data_source_id = (SELECT data_source_id FROM data_source WHERE source_name = 'Synthetic data generator') WHERE data_source_id IS NULL;

-- 3) Now make it required
ALTER TABLE temperature_reading ALTER COLUMN data_source_id SET NOT NULL;
ALTER TABLE coolant_flow        ALTER COLUMN data_source_id SET NOT NULL;
ALTER TABLE electrical_reading  ALTER COLUMN data_source_id SET NOT NULL;
ALTER TABLE aging_record        ALTER COLUMN data_source_id SET NOT NULL;
ALTER TABLE cfd_simulation      ALTER COLUMN data_source_id SET NOT NULL;
