-- Step 15: app_user (role-based login)
-- Safe to re-run: drops and recreates only app_user.
-- Nothing references app_user yet, so DROP is safe.

DROP TABLE IF EXISTS app_user CASCADE;

CREATE TABLE app_user (
    user_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    full_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    -- Store only a hash, never the password. FastAPI will create the hash (bcrypt, ~60 chars).
    -- The length check only blocks obviously short plain-text values; it is not a security guarantee.
    password_hash  TEXT NOT NULL CHECK (length(password_hash) >= 20),
    role           VARCHAR(20) NOT NULL
                   CHECK (role IN ('ADMIN', 'BMS_ENGINEER', 'FLEET_OPERATOR',
                                   'SERVICE_TECHNICIAN', 'RESEARCHER')),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at  TIMESTAMPTZ
);

-- SAMPLE ROWS (fake). The hash is a placeholder, so none of these users can log in.
-- Real users will be created through the API with properly hashed passwords.
INSERT INTO app_user (username, full_name, email, password_hash, role) VALUES
 ('admin1',      'SAMPLE Admin',              'admin1@example.com',      'SAMPLE_HASH_NOT_A_REAL_PASSWORD', 'ADMIN'),
 ('engineer1',   'SAMPLE BMS Engineer',       'engineer1@example.com',   'SAMPLE_HASH_NOT_A_REAL_PASSWORD', 'BMS_ENGINEER'),
 ('fleet1',      'SAMPLE Fleet Operator',     'fleet1@example.com',      'SAMPLE_HASH_NOT_A_REAL_PASSWORD', 'FLEET_OPERATOR'),
 ('technician1', 'SAMPLE Service Technician', 'technician1@example.com', 'SAMPLE_HASH_NOT_A_REAL_PASSWORD', 'SERVICE_TECHNICIAN'),
 ('researcher1', 'SAMPLE Researcher',         'researcher1@example.com', 'SAMPLE_HASH_NOT_A_REAL_PASSWORD', 'RESEARCHER');
