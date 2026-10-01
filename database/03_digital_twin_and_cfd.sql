-- 03_digital_twin_and_cfd.sql
-- Drops only these two tables (safe while they hold no real data).
DROP TABLE IF EXISTS cfd_simulation;
DROP TABLE IF EXISTS digital_twin;

-- One digital twin per battery (UNIQUE on battery_id makes it 1:1)
CREATE TABLE digital_twin (
    twin_id            INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    battery_id         INT NOT NULL UNIQUE REFERENCES battery(battery_id),
    model_version      VARCHAR(30) NOT NULL,
    last_synced_at     TIMESTAMPTZ,
    simulated_soh_pct  NUMERIC(5,2) CHECK (simulated_soh_pct BETWEEN 0 AND 100)
);

-- Many CFD simulation runs per digital twin
CREATE TABLE cfd_simulation (
    simulation_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    twin_id            INT NOT NULL REFERENCES digital_twin(twin_id),
    run_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    flow_rate_lpm      NUMERIC(6,2) NOT NULL CHECK (flow_rate_lpm > 0),
    inlet_temp_c       NUMERIC(5,2) NOT NULL,
    max_temp_c         NUMERIC(5,2) NOT NULL,
    avg_temp_c         NUMERIC(5,2) NOT NULL,
    pressure_drop_kpa  NUMERIC(7,2) CHECK (pressure_drop_kpa >= 0),
    CONSTRAINT chk_cfd_max_ge_avg CHECK (max_temp_c >= avg_temp_c)
);

-- SYNTHETIC sample digital twins (invented for the prototype)
INSERT INTO digital_twin (battery_id, model_version, last_synced_at, simulated_soh_pct)
SELECT b.battery_id, 'v1.0', '2026-10-01 09:00:00+05:30'::timestamptz, v.soh
FROM (VALUES
    ('VC-NMC-0001', 97.5),
    ('EC-LFP-0001', 98.2)
) AS v(serial, soh)
JOIN battery b ON b.serial_number = v.serial;

-- SYNTHETIC sample CFD results (invented, not from a real simulation)
INSERT INTO cfd_simulation (twin_id, run_at, flow_rate_lpm, inlet_temp_c, max_temp_c, avg_temp_c, pressure_drop_kpa)
SELECT d.twin_id, v.run_at::timestamptz, v.flow, v.inlet, v.maxt, v.avgt, v.dp
FROM (VALUES
    ('VC-NMC-0001', '2026-10-01 08:00:00+05:30',  8.0, 25.0, 38.2, 33.5, 12.5),
    ('VC-NMC-0001', '2026-10-01 08:30:00+05:30',  6.0, 25.0, 42.6, 36.1,  8.1),
    ('EC-LFP-0001', '2026-10-01 08:00:00+05:30', 10.0, 25.0, 33.4, 30.2, 15.3)
) AS v(serial, run_at, flow, inlet, maxt, avgt, dp)
JOIN battery b      ON b.serial_number = v.serial
JOIN digital_twin d ON d.battery_id = b.battery_id;
