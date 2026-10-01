-- 02_sensor_and_readings.sql
-- Drops only these three tables (safe while they hold no real data).
DROP TABLE IF EXISTS coolant_flow;
DROP TABLE IF EXISTS temperature_reading;
DROP TABLE IF EXISTS sensor;

-- A sensor mounted on a battery
CREATE TABLE sensor (
    sensor_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    battery_id   INT NOT NULL REFERENCES battery(battery_id),
    sensor_type  VARCHAR(20) NOT NULL
                 CHECK (sensor_type IN ('TEMPERATURE', 'COOLANT_FLOW', 'VOLTAGE', 'CURRENT')),
    location     VARCHAR(50) NOT NULL,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (battery_id, location)
);

-- Temperature readings: identified by sensor + time (weak entity)
CREATE TABLE temperature_reading (
    sensor_id      INT NOT NULL REFERENCES sensor(sensor_id),
    recorded_at    TIMESTAMPTZ NOT NULL,
    temperature_c  NUMERIC(5,2) NOT NULL CHECK (temperature_c BETWEEN -50 AND 200),
    PRIMARY KEY (sensor_id, recorded_at)
);

-- Coolant flow readings: also identified by sensor + time
CREATE TABLE coolant_flow (
    sensor_id      INT NOT NULL REFERENCES sensor(sensor_id),
    recorded_at    TIMESTAMPTZ NOT NULL,
    flow_rate_lpm  NUMERIC(6,2) NOT NULL CHECK (flow_rate_lpm >= 0),
    inlet_temp_c   NUMERIC(5,2),
    PRIMARY KEY (sensor_id, recorded_at)
);

-- SYNTHETIC sample sensors (invented for the prototype)
INSERT INTO sensor (battery_id, sensor_type, location)
SELECT b.battery_id, v.sensor_type, v.location
FROM (VALUES
    ('VC-NMC-0001', 'TEMPERATURE',  'CELL_1'),
    ('VC-NMC-0001', 'TEMPERATURE',  'CELL_2'),
    ('VC-NMC-0001', 'COOLANT_FLOW', 'COOLANT_LOOP'),
    ('EC-LFP-0001', 'TEMPERATURE',  'CELL_1'),
    ('EC-LFP-0001', 'COOLANT_FLOW', 'COOLANT_LOOP')
) AS v(serial, sensor_type, location)
JOIN battery b ON b.serial_number = v.serial;

-- SYNTHETIC sample temperature readings
INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c)
SELECT s.sensor_id, v.recorded_at::timestamptz, v.temperature_c
FROM (VALUES
    ('VC-NMC-0001', 'CELL_1', '2026-10-01 09:00:00+05:30', 30.5),
    ('VC-NMC-0001', 'CELL_1', '2026-10-01 09:01:00+05:30', 31.0),
    ('VC-NMC-0001', 'CELL_1', '2026-10-01 09:02:00+05:30', 31.4),
    ('VC-NMC-0001', 'CELL_2', '2026-10-01 09:00:00+05:30', 30.8),
    ('VC-NMC-0001', 'CELL_2', '2026-10-01 09:01:00+05:30', 31.2),
    ('VC-NMC-0001', 'CELL_2', '2026-10-01 09:02:00+05:30', 31.9),
    ('EC-LFP-0001', 'CELL_1', '2026-10-01 09:00:00+05:30', 28.0),
    ('EC-LFP-0001', 'CELL_1', '2026-10-01 09:01:00+05:30', 28.3),
    ('EC-LFP-0001', 'CELL_1', '2026-10-01 09:02:00+05:30', 28.6)
) AS v(serial, location, recorded_at, temperature_c)
JOIN battery b ON b.serial_number = v.serial
JOIN sensor s  ON s.battery_id = b.battery_id AND s.location = v.location;

-- SYNTHETIC sample coolant flow readings
INSERT INTO coolant_flow (sensor_id, recorded_at, flow_rate_lpm, inlet_temp_c)
SELECT s.sensor_id, v.recorded_at::timestamptz, v.flow_rate_lpm, v.inlet_temp_c
FROM (VALUES
    ('VC-NMC-0001', 'COOLANT_LOOP', '2026-10-01 09:00:00+05:30', 8.0, 25.0),
    ('VC-NMC-0001', 'COOLANT_LOOP', '2026-10-01 09:01:00+05:30', 8.1, 25.0),
    ('VC-NMC-0001', 'COOLANT_LOOP', '2026-10-01 09:02:00+05:30', 7.9, 25.2),
    ('EC-LFP-0001', 'COOLANT_LOOP', '2026-10-01 09:00:00+05:30', 10.0, 25.0),
    ('EC-LFP-0001', 'COOLANT_LOOP', '2026-10-01 09:01:00+05:30', 10.1, 25.1),
    ('EC-LFP-0001', 'COOLANT_LOOP', '2026-10-01 09:02:00+05:30', 9.9, 25.1)
) AS v(serial, location, recorded_at, flow_rate_lpm, inlet_temp_c)
JOIN battery b ON b.serial_number = v.serial
JOIN sensor s  ON s.battery_id = b.battery_id AND s.location = v.location;
