-- Step 18: Automatic alert trigger
-- When a risk assessment with final level HIGH or CRITICAL is inserted,
-- the database itself creates an OPEN alert with the matching priority.
-- Safe to re-run: replaces the function and recreates the trigger.

CREATE OR REPLACE FUNCTION fn_create_alert_for_risk()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_serial       TEXT;
    v_risk_type    TEXT;
    v_priority_id  INTEGER;
BEGIN
    -- Only HIGH and CRITICAL raise an alert; LOW and MEDIUM do not.
    IF NEW.final_risk_level IN ('HIGH', 'CRITICAL') THEN

        SELECT b.serial_number, m.risk_type
          INTO v_serial, v_risk_type
          FROM prediction_result pr
          JOIN battery b  ON pr.battery_id = b.battery_id
          JOIN ai_model m ON pr.model_id = m.model_id
         WHERE pr.prediction_id = NEW.prediction_id;

        -- priority_code in alert_priority matches the risk level name (HIGH, CRITICAL)
        SELECT alert_priority_id
          INTO v_priority_id
          FROM alert_priority
         WHERE priority_code = NEW.final_risk_level;

        INSERT INTO alert (assessment_id, alert_priority_id, message, status)
        VALUES (
            NEW.assessment_id,
            v_priority_id,
            format('AUTO: %s %s risk on %s',
                   NEW.final_risk_level, lower(v_risk_type), v_serial),
            'OPEN'
        );
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_alert_on_risk ON risk_assessment;

CREATE TRIGGER trg_alert_on_risk
AFTER INSERT ON risk_assessment
FOR EACH ROW
EXECUTE FUNCTION fn_create_alert_for_risk();
