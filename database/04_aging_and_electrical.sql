-- 04_aging_and_electrical.sql
-- Adds aging measurements and electrical (voltage/current) readings.
-- Also CHANGES an existing table (sensor) using ALTER, so no data is lost.
-- Safe to re-run.

-- 1) Change the allowed sensor types: replace VOLTAGE/CURRENT with one ELECTRICAL type
--    (one BMS sensor reports voltage and current together). Existing rows stay valid.
ALTER TABLE sensor DROP CONSTRAINT IF EXISTS sensor_sensor_type_check;
ALTER TABLE sensor ADD CONSTRAINT sensor_sensor_type_check
    CHECK (sensor_type IN ('TEMPERATURE', 'COOLANT_FLOW', 'ELECTRICAL'));

-- 2) New tables (drop only these two)
DROP TABLE IF EXISTS electrical_reading;
DROP TABLE IF EXISTS aging_record;

-- Periodic aging measurements per battery
CREATE TABLE aging_record (
    aging_id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    battery_id                INT NOT NULL REFERENCES battery(battery_id),
    measured_at               TIMESTAMPTZ NOT NULL,
    cycle_count               INT NOT NULL CHECK (cycle_count >= 0),
    calendar_age_days         INT NOT NULL CHECK (calendar_age_days >= 0),
    capacity_ah               NUMERIC(8,2) NOT NULL CHECK (capacity_ah > 0),
    internal_resistance_mohm  NUMERIC(8,3) NOT NULL CHECK (internal_resistance_mohm > 0),
    UNIQUE (battery_id, measured_at)
);
-- Note: state of health is NOT stored. It is calculated as capacity_ah / nominal_capacity_ah.

-- Voltage and current readings: identified by sensor + time (weak entity)
CREATE TABLE electrical_reading (
    sensor_id    INT NOT NULL REFERENCES sensor(sensor_id),
    recorded_at  TIMESTAMPTZ NOT NULL,
    voltage_v    NUMERIC(6,3) NOT NULL CHECK (voltage_v BETWEEN 0 AND 1000),
    current_a    NUMERIC(8,3) NOT NULL,
    PRIMARY KEY (sensor_id, recorded_at)
);

-- 3) SYNTHETIC sample data (invented for the prototype)
INSERT INTO sensor (battery_id, sensor_type, location)
SELECT b.battery_id, 'ELECTRICAL', 'BMS_MAIN'
FROM battery b
WHERE b.serial_number IN ('VC-NMC-0001', 'EC-LFP-0001')
ON CONFLICT (battery_id, location) DO NOTHING;

INSERT INTO electrical_reading (sensor_id, recorded_at, voltage_v, current_a)
SELECT s.sensor_id, v.recorded_at::timestamptz, v.voltage_v, v.current_a
FROM (VALUES
    ('VC-NMC-0001', '2026-10-01 09:00:00+05:30', 355.100, 120.500),
    ('VC-NMC-0001', '2026-10-01 09:01:00+05:30', 354.800, 118.200),
    ('VC-NMC-0001', '2026-10-01 09:02:00+05:30', 354.600, 121.000),
    ('EC-LFP-0001', '2026-10-01 09:00:00+05:30', 320.400,  80.000),
    ('EC-LFP-0001', '2026-10-01 09:01:00+05:30', 320.100,  82.500),
    ('EC-LFP-0001', '2026-10-01 09:02:00+05:30', 320.000,  81.100)
) AS v(serial, recorded_at, voltage_v, current_a)
JOIN battery b ON b.serial_number = v.serial
JOIN sensor s  ON s.battery_id = b.battery_id AND s.location = 'BMS_MAIN';

INSERT INTO aging_record (battery_id, measured_at, cycle_count, calendar_age_days, capacity_ah, internal_resistance_mohm)
SELECT b.battery_id, v.measured_at::timestamptz, v.cycles, v.age_days, v.cap, v.res
FROM (VALUES
    ('VC-NMC-0001', '2025-01-15 12:00:00+05:30', 150, 366, 73.60, 45.200),
    ('VC-NMC-0001', '2026-01-15 12:00:00+05:30', 320, 731, 71.80, 49.800),
    ('EC-LFP-0001', '2025-02-10 12:00:00+05:30', 180, 366, 99.10, 38.000),
    ('EC-LFP-0001', '2026-02-10 12:00:00+05:30', 380, 731, 97.90, 39.500),
    ('PN-NCA-0001', '2026-03-05 12:00:00+05:30', 400, 731, 56.90, 61.000)
) AS v(serial, measured_at, cycles, age_days, cap, res)
JOIN battery b ON b.serial_number = v.serial;
