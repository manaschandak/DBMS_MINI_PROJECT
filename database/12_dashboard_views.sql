-- Step 17: Dashboard views
-- Safe to re-run: drops and recreates only these 5 views (in dependency order).

DROP VIEW IF EXISTS v_chemistry_comparison;
DROP VIEW IF EXISTS v_risk_distribution;
DROP VIEW IF EXISTS v_open_alerts;
DROP VIEW IF EXISTS v_battery_overview;
DROP VIEW IF EXISTS v_latest_risk;

-- 1. Most recent final risk level for each battery and risk type (THERMAL / HEALTH)
CREATE VIEW v_latest_risk AS
SELECT DISTINCT ON (pr.battery_id, m.risk_type)
       pr.battery_id,
       m.risk_type,
       ra.final_risk_level,
       ra.rule_override,
       ra.assessed_at
FROM risk_assessment ra
JOIN prediction_result pr ON ra.prediction_id = pr.prediction_id
JOIN ai_model m           ON pr.model_id = m.model_id
ORDER BY pr.battery_id, m.risk_type, ra.assessed_at DESC;

-- 2. One row per battery: the main fleet table on the dashboard
CREATE VIEW v_battery_overview AS
SELECT
    b.battery_id,
    b.serial_number,
    mf.manufacturer_name,
    c.chemistry_code,
    b.status,
    (SELECT max(lt.temperature_c)
       FROM sensor s
       CROSS JOIN LATERAL (
            SELECT tr.temperature_c
            FROM temperature_reading tr
            WHERE tr.sensor_id = s.sensor_id
            ORDER BY tr.recorded_at DESC
            LIMIT 1) lt
      WHERE s.battery_id = b.battery_id) AS latest_max_temp_c,
    lt_risk.final_risk_level AS thermal_risk,
    lh_risk.final_risk_level AS health_risk,
    (SELECT count(*)
       FROM alert a
       JOIN risk_assessment ra ON a.assessment_id = ra.assessment_id
       JOIN prediction_result pr ON ra.prediction_id = pr.prediction_id
      WHERE pr.battery_id = b.battery_id
        AND a.status = 'OPEN') AS open_alerts
FROM battery b
JOIN manufacturer mf ON b.manufacturer_id = mf.manufacturer_id
JOIN chemistry c     ON b.chemistry_id = c.chemistry_id
LEFT JOIN v_latest_risk lt_risk
       ON lt_risk.battery_id = b.battery_id AND lt_risk.risk_type = 'THERMAL'
LEFT JOIN v_latest_risk lh_risk
       ON lh_risk.battery_id = b.battery_id AND lh_risk.risk_type = 'HEALTH';

-- 3. Alerts still open, with priority and battery (order by severity_level when querying)
CREATE VIEW v_open_alerts AS
SELECT
    a.alert_id,
    ap.priority_code,
    ap.severity_level,
    b.serial_number,
    ra.final_risk_level,
    a.message,
    a.status,
    a.created_at
FROM alert a
JOIN alert_priority ap    ON a.alert_priority_id = ap.alert_priority_id
JOIN risk_assessment ra   ON a.assessment_id = ra.assessment_id
JOIN prediction_result pr ON ra.prediction_id = pr.prediction_id
JOIN battery b            ON pr.battery_id = b.battery_id
WHERE a.status = 'OPEN';

-- 4. How many batteries are at each risk level (latest assessment per battery)
CREATE VIEW v_risk_distribution AS
SELECT risk_type, final_risk_level, count(*) AS battery_count
FROM v_latest_risk
GROUP BY risk_type, final_risk_level;

-- 5. NMC vs LFP vs NCA, using each battery's latest aging record and its peak temperature
CREATE VIEW v_chemistry_comparison AS
WITH latest_aging AS (
    SELECT DISTINCT ON (battery_id)
           battery_id, cycle_count, internal_resistance_mohm, capacity_ah
    FROM aging_record
    ORDER BY battery_id, measured_at DESC
),
peak_temp AS (
    SELECT s.battery_id, max(tr.temperature_c) AS peak_temp_c
    FROM temperature_reading tr
    JOIN sensor s ON tr.sensor_id = s.sensor_id
    GROUP BY s.battery_id
)
SELECT
    c.chemistry_code,
    c.chemistry_name,
    count(DISTINCT b.battery_id)                                AS battery_count,
    round(avg(la.cycle_count), 0)                               AS avg_cycles,
    round(avg(la.internal_resistance_mohm), 2)                  AS avg_resistance_mohm,
    round(avg(la.capacity_ah / b.nominal_capacity_ah * 100), 1) AS avg_capacity_pct_of_nominal,
    round(avg(pt.peak_temp_c), 1)                               AS avg_peak_temp_c,
    max(pt.peak_temp_c)                                         AS max_peak_temp_c
FROM chemistry c
LEFT JOIN battery b      ON b.chemistry_id = c.chemistry_id
LEFT JOIN latest_aging la ON la.battery_id = b.battery_id
LEFT JOIN peak_temp pt    ON pt.battery_id = b.battery_id
GROUP BY c.chemistry_code, c.chemistry_name;
