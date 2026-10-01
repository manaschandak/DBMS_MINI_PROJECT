-- 01_manufacturer_chemistry_battery.sql
-- Run from the project root:
--   psql -U postgres -d battery_db -f database/01_manufacturer_chemistry_battery.sql
-- The DROP lines are safe ONLY while these tables hold no real data (early development).
-- Once real data exists we change tables with ALTER instead.

DROP TABLE IF EXISTS battery;
DROP TABLE IF EXISTS manufacturer;
DROP TABLE IF EXISTS chemistry;

-- Who makes the batteries
CREATE TABLE manufacturer (
    manufacturer_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    manufacturer_name  VARCHAR(100) NOT NULL UNIQUE,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Battery chemistry (NMC, LFP, NCA)
CREATE TABLE chemistry (
    chemistry_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chemistry_code  VARCHAR(10)  NOT NULL UNIQUE,
    chemistry_name  VARCHAR(100) NOT NULL
);

-- A battery pack or cell
CREATE TABLE battery (
    battery_id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    serial_number        VARCHAR(50)  NOT NULL UNIQUE,
    battery_type         VARCHAR(10)  NOT NULL DEFAULT 'PACK'
                         CHECK (battery_type IN ('PACK', 'CELL')),
    manufacturer_id      INT NOT NULL REFERENCES manufacturer(manufacturer_id),
    chemistry_id         INT NOT NULL REFERENCES chemistry(chemistry_id),
    nominal_capacity_ah  NUMERIC(8,2) NOT NULL CHECK (nominal_capacity_ah > 0),
    install_date         DATE,
    status               VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
                         CHECK (status IN ('ACTIVE', 'MAINTENANCE', 'RETIRED'))
);

-- Sample data. Manufacturers and chemistries come from the project document.
INSERT INTO chemistry (chemistry_code, chemistry_name) VALUES
    ('NMC', 'Lithium Nickel Manganese Cobalt Oxide'),
    ('LFP', 'Lithium Iron Phosphate'),
    ('NCA', 'Lithium Nickel Cobalt Aluminum Oxide');

INSERT INTO manufacturer (manufacturer_name) VALUES
    ('VoltCore Energy'),
    ('ElectroCell Ltd'),
    ('PowerNova Systems'),
    ('GreenLithium Tech'),
    ('FutureCharge Inc');

-- SYNTHETIC sample batteries (invented for the prototype, not real measurements)
INSERT INTO battery (serial_number, manufacturer_id, chemistry_id, nominal_capacity_ah, install_date) VALUES
    ('VC-NMC-0001',
        (SELECT manufacturer_id FROM manufacturer WHERE manufacturer_name = 'VoltCore Energy'),
        (SELECT chemistry_id FROM chemistry WHERE chemistry_code = 'NMC'), 75.00, '2024-01-15'),
    ('EC-LFP-0001',
        (SELECT manufacturer_id FROM manufacturer WHERE manufacturer_name = 'ElectroCell Ltd'),
        (SELECT chemistry_id FROM chemistry WHERE chemistry_code = 'LFP'), 100.00, '2024-02-10'),
    ('PN-NCA-0001',
        (SELECT manufacturer_id FROM manufacturer WHERE manufacturer_name = 'PowerNova Systems'),
        (SELECT chemistry_id FROM chemistry WHERE chemistry_code = 'NCA'), 60.00, '2024-03-05'),
    ('GL-NMC-0001',
        (SELECT manufacturer_id FROM manufacturer WHERE manufacturer_name = 'GreenLithium Tech'),
        (SELECT chemistry_id FROM chemistry WHERE chemistry_code = 'NMC'), 80.00, '2024-04-20'),
    ('FC-LFP-0001',
        (SELECT manufacturer_id FROM manufacturer WHERE manufacturer_name = 'FutureCharge Inc'),
        (SELECT chemistry_id FROM chemistry WHERE chemistry_code = 'LFP'), 120.00, '2024-05-12');
