"""Backend tests, stage 2: write endpoints. Runs against battery_db.

Every row created here is labelled TEST (serial 'TEST-...', manufacturer 'TEST_...',
chemistry 'TST...') and is deleted afterwards, child tables first.
Login tests need the seeded users' password in an environment variable
(PowerShell, this terminal only, never commit it):
    $env:TEST_PASSWORD = "..."
Run from the backend folder:  python -m pytest tests -q --tb=short -rs
Tests run in file order and share the TEST battery created in the ctx fixture.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_db
from app.main import app

client = TestClient(app)
TAG = uuid.uuid4().hex[:6]
SERIAL = f"TEST-{TAG}"
OK = (200, 201)
NOW = datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat()


def run_sql(sql, **params):
    gen = get_db()
    db = next(gen)
    try:
        res = db.execute(text(sql), params)
        rows = res.fetchall() if res.returns_rows else None
        db.commit()
        return rows
    finally:
        gen.close()


def pick(data, *keys):
    for k in keys:
        if k in data:
            return data[k]
    raise AssertionError(f"none of {keys} in response: {data}")


# ---- cleanup: child tables first (almost every foreign key is NO ACTION) ----
B = "SELECT battery_id FROM battery WHERE starts_with(serial_number, 'TEST-')"
S = f"SELECT sensor_id FROM sensor WHERE battery_id IN ({B})"
P = f"SELECT prediction_id FROM prediction_result WHERE battery_id IN ({B})"
A = f"SELECT assessment_id FROM risk_assessment WHERE prediction_id IN ({P})"
AN = f"SELECT anomaly_id FROM sensor_anomaly WHERE sensor_id IN ({S})"
T = f"SELECT twin_id FROM digital_twin WHERE battery_id IN ({B})"
CLEANUP = [
    f"DELETE FROM recommendation WHERE assessment_id IN ({A}) OR anomaly_id IN ({AN})",
    f"DELETE FROM alert WHERE assessment_id IN ({A})",
    f"DELETE FROM risk_assessment WHERE prediction_id IN ({P})",
    f"DELETE FROM prediction_result WHERE battery_id IN ({B})",  # feedback cascades
    f"DELETE FROM sensor_anomaly WHERE sensor_id IN ({S})",
    f"DELETE FROM temperature_reading WHERE sensor_id IN ({S})",
    f"DELETE FROM coolant_flow WHERE sensor_id IN ({S})",
    f"DELETE FROM electrical_reading WHERE sensor_id IN ({S})",
    f"DELETE FROM cfd_simulation WHERE twin_id IN ({T})",
    f"DELETE FROM digital_twin WHERE battery_id IN ({B})",
    f"DELETE FROM aging_record WHERE battery_id IN ({B})",
    f"DELETE FROM sensor WHERE battery_id IN ({B})",
    "DELETE FROM battery WHERE starts_with(serial_number, 'TEST-')",
    "DELETE FROM chemistry WHERE starts_with(chemistry_code, 'TST')",
    "DELETE FROM manufacturer WHERE starts_with(manufacturer_name, 'TEST_')",
]


def cleanup(perf_baseline):
    for sql in CLEANUP:
        run_sql(sql)
    run_sql(
        "DELETE FROM model_performance WHERE performance_id > :p AND evaluation_type = 'LIVE_FEEDBACK'",
        p=perf_baseline,
    )


def battery_body(ctx, **over):
    body = {
        "serial_number": SERIAL,
        "battery_type": "PACK",
        "manufacturer_id": ctx["manufacturer_id"],
        "chemistry_id": ctx["chemistry_id"],
        "nominal_capacity_ah": 100.0,
        "status": "ACTIVE",
    }
    body.update(over)
    return body


@pytest.fixture(scope="module")
def ctx():
    baseline = run_sql("SELECT coalesce(max(performance_id), 0) FROM model_performance")[0][0]
    cleanup(baseline)  # also removes leftovers of an earlier crashed run
    c = {}
    r = client.post("/api/manufacturers", json={"manufacturer_name": f"TEST_Mfr_{TAG}"})
    assert r.status_code in OK, r.text
    c["manufacturer_id"] = pick(r.json(), "manufacturer_id", "id")
    r = client.post("/api/chemistries", json={"chemistry_code": f"TST{TAG[:4]}", "chemistry_name": "TEST chemistry"})
    assert r.status_code in OK, r.text
    c["chemistry_id"] = pick(r.json(), "chemistry_id", "id")
    r = client.post("/api/batteries", json=battery_body(c))
    assert r.status_code in OK, r.text
    c["battery_id"] = pick(r.json(), "battery_id", "id")
    r = client.post(f"/api/batteries/{c['battery_id']}/sensors", json={"sensor_type": "TEMPERATURE", "location": "TEST_loc"})
    assert r.status_code in OK, r.text
    c["sensor_id"] = pick(r.json(), "sensor_id", "id")
    r = client.post("/api/digital-twins", json={"battery_id": c["battery_id"], "model_version": "TEST_v1"})
    assert r.status_code in OK, r.text
    c["twin_id"] = pick(r.json(), "twin_id", "id")
    yield c
    cleanup(baseline)
    left = run_sql("SELECT count(*) FROM battery WHERE starts_with(serial_number, 'TEST-')")[0][0]
    assert left == 0, "TEST rows were left behind"


@pytest.fixture(scope="module")
def admin_headers():
    pw = os.environ.get("TEST_PASSWORD")
    if not pw:
        pytest.skip('set $env:TEST_PASSWORD to run the login tests')
    r = client.post("/api/auth/login", json={"username": "admin1", "password": pw})
    assert r.status_code == 200, "login as admin1 failed: " + r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


# ---------------- manufacturers ----------------
def test_manufacturer_duplicate_rejected(ctx):
    r = client.post("/api/manufacturers", json={"manufacturer_name": f"TEST_Mfr_{TAG}"})
    assert r.status_code == 409, r.text


def test_manufacturer_empty_name_rejected():
    r = client.post("/api/manufacturers", json={"manufacturer_name": ""})
    assert r.status_code == 422, r.text


def test_manufacturer_update(ctx):
    r = client.put(f"/api/manufacturers/{ctx['manufacturer_id']}", json={"manufacturer_name": f"TEST_Mfr_{TAG}_x"})
    assert r.status_code in OK, r.text


def test_manufacturer_update_missing():
    r = client.put("/api/manufacturers/999999", json={"manufacturer_name": "TEST_nobody"})
    assert r.status_code == 404, r.text


def test_manufacturer_delete_in_use_rejected(ctx):
    r = client.delete(f"/api/manufacturers/{ctx['manufacturer_id']}")
    assert r.status_code in (409, 422), r.text


def test_manufacturer_create_and_delete():
    r = client.post("/api/manufacturers", json={"manufacturer_name": f"TEST_Tmp_{TAG}"})
    assert r.status_code in OK, r.text
    mid = pick(r.json(), "manufacturer_id", "id")
    assert client.delete(f"/api/manufacturers/{mid}").status_code in (200, 204)
    assert client.delete(f"/api/manufacturers/{mid}").status_code == 404


# ---------------- chemistries ----------------
def test_chemistry_duplicate_rejected(ctx):
    r = client.post("/api/chemistries", json={"chemistry_code": f"TST{TAG[:4]}", "chemistry_name": "TEST again"})
    assert r.status_code == 409, r.text


def test_chemistry_empty_code_rejected():
    r = client.post("/api/chemistries", json={"chemistry_code": "", "chemistry_name": "TEST"})
    assert r.status_code == 422, r.text


# ---------------- batteries ----------------
def test_battery_get(ctx):
    r = client.get(f"/api/batteries/{ctx['battery_id']}")
    assert r.status_code == 200, r.text
    assert r.json()["serial_number"] == SERIAL


def test_battery_duplicate_serial_rejected(ctx):
    r = client.post("/api/batteries", json=battery_body(ctx))
    assert r.status_code == 409, r.text


def test_battery_invalid_status_rejected(ctx):
    r = client.post("/api/batteries", json=battery_body(ctx, serial_number=f"TEST-{TAG}-bad", status="BROKEN"))
    assert r.status_code == 422, r.text


def test_battery_update(ctx):
    r = client.put(f"/api/batteries/{ctx['battery_id']}", json=battery_body(ctx, status="MAINTENANCE"))
    assert r.status_code in OK, r.text
    assert client.get(f"/api/batteries/{ctx['battery_id']}").json()["status"] == "MAINTENANCE"
    r = client.put(f"/api/batteries/{ctx['battery_id']}", json=battery_body(ctx, status="ACTIVE"))
    assert r.status_code in OK, r.text


def test_battery_update_missing(ctx):
    r = client.put("/api/batteries/999999", json=battery_body(ctx, serial_number=f"TEST-{TAG}-none"))
    assert r.status_code == 404, r.text


def test_battery_delete_with_children_rejected(ctx):
    r = client.delete(f"/api/batteries/{ctx['battery_id']}")
    assert r.status_code in (409, 422), r.text


def test_battery_create_and_delete(ctx):
    r = client.post("/api/batteries", json=battery_body(ctx, serial_number=f"TEST-{TAG}-tmp"))
    assert r.status_code in OK, r.text
    bid = pick(r.json(), "battery_id", "id")
    assert client.delete(f"/api/batteries/{bid}").status_code in (200, 204)
    assert client.get(f"/api/batteries/{bid}").status_code == 404


# ---------------- sensors and readings ----------------
def test_sensor_invalid_type_rejected(ctx):
    r = client.post(f"/api/batteries/{ctx['battery_id']}/sensors", json={"sensor_type": "BAD", "location": "TEST_loc"})
    assert r.status_code == 422, r.text


def test_sensor_unknown_battery():
    r = client.post("/api/batteries/999999/sensors", json={"sensor_type": "TEMPERATURE", "location": "TEST_loc"})
    assert r.status_code == 404, r.text


def test_sensor_listed(ctx):
    r = client.get(f"/api/batteries/{ctx['battery_id']}/sensors")
    assert r.status_code == 200, r.text
    assert str(ctx["sensor_id"]) in r.text


def reading(ctx, temp, when):
    return {"sensor_id": ctx["sensor_id"], "recorded_at": iso(when), "temperature_c": temp, "data_source_id": 1}


def test_readings_batch_ok(ctx):
    r = client.post("/api/readings", json={"temperature": [reading(ctx, 30.0, NOW - timedelta(hours=2))]})
    assert r.status_code in OK, r.text
    r = client.get(f"/api/sensors/{ctx['sensor_id']}/readings")
    assert r.status_code == 200, r.text


def test_readings_empty_batch_rejected():
    r = client.post("/api/readings", json={})
    assert r.status_code == 422, r.text


def test_readings_unknown_sensor_rejected(ctx):
    bad = reading(ctx, 30.0, NOW)
    bad["sensor_id"] = 999999
    r = client.post("/api/readings", json={"temperature": [bad]})
    assert r.status_code in (404, 409, 422), r.text


def test_readings_out_of_range_rejected(ctx):
    r = client.post("/api/readings", json={"temperature": [reading(ctx, 500.0, NOW)]})
    assert r.status_code == 422, r.text


# ---------------- aging ----------------
def aging_body(**over):
    body = {"measured_at": iso(NOW), "cycle_count": 10, "calendar_age_days": 30,
            "capacity_ah": 95.0, "internal_resistance_mohm": 1.5, "data_source_id": 1}
    body.update(over)
    return body


def test_aging_create_and_latest(ctx):
    r = client.post(f"/api/batteries/{ctx['battery_id']}/aging", json=aging_body())
    assert r.status_code in OK, r.text
    assert client.get(f"/api/batteries/{ctx['battery_id']}/aging/latest").status_code == 200


def test_aging_zero_capacity_rejected(ctx):
    r = client.post(f"/api/batteries/{ctx['battery_id']}/aging", json=aging_body(capacity_ah=0))
    assert r.status_code == 422, r.text


def test_aging_unknown_battery():
    r = client.post("/api/batteries/999999/aging", json=aging_body())
    assert r.status_code == 404, r.text


# ---------------- digital twin and CFD ----------------
def test_twin_duplicate_rejected(ctx):
    r = client.post("/api/digital-twins", json={"battery_id": ctx["battery_id"], "model_version": "TEST_v2"})
    assert r.status_code == 409, r.text


def test_twin_unknown_battery_rejected():
    r = client.post("/api/digital-twins", json={"battery_id": 999999, "model_version": "TEST_v1"})
    assert r.status_code in (404, 409, 422), r.text


def cfd_body(ctx, **over):
    body = {"twin_id": ctx["twin_id"], "flow_rate_lpm": 5.0, "inlet_temp_c": 25.0,
            "max_temp_c": 40.0, "avg_temp_c": 35.0, "data_source_id": 4}
    body.update(over)
    return body


def test_cfd_create(ctx):
    r = client.post("/api/cfd-simulations", json=cfd_body(ctx))
    assert r.status_code in OK, r.text


def test_cfd_max_below_avg_rejected(ctx):
    r = client.post("/api/cfd-simulations", json=cfd_body(ctx, max_temp_c=30.0, avg_temp_c=35.0))
    assert r.status_code == 422, r.text


# ---------------- predictions, alerts, feedback ----------------
def test_prediction_thermal_normal(ctx):
    r = client.post("/api/predictions/risk", json={"battery_id": ctx["battery_id"], "risk_type": "THERMAL"})
    assert r.status_code in OK, r.text
    assert "final_risk_level" in r.json()
    ctx["prediction_id"] = pick(r.json(), "prediction_id", "id")


def test_prediction_health(ctx):
    r = client.post("/api/predictions/risk", json={"battery_id": ctx["battery_id"], "risk_type": "HEALTH"})
    assert r.status_code in OK, r.text
    assert "final_risk_level" in r.json()


def test_prediction_hard_limit_forces_critical(ctx):
    r = client.post("/api/readings", json={"temperature": [reading(ctx, 65.0, NOW - timedelta(hours=1))]})
    assert r.status_code in OK, r.text
    r = client.post("/api/predictions/risk", json={"battery_id": ctx["battery_id"], "risk_type": "THERMAL"})
    assert r.status_code in OK, r.text
    assert r.json()["final_risk_level"] == "CRITICAL"


def test_prediction_unknown_battery():
    r = client.post("/api/predictions/risk", json={"battery_id": 999999, "risk_type": "THERMAL"})
    assert r.status_code == 404, r.text


def test_prediction_invalid_risk_type(ctx):
    r = client.post("/api/predictions/risk", json={"battery_id": ctx["battery_id"], "risk_type": "FOO"})
    assert r.status_code == 422, r.text


def test_critical_prediction_created_alert(ctx):
    r = client.get("/api/alerts", params={"limit": 200})
    assert r.status_code == 200, r.text
    mine = [a for a in r.json() if a["serial_number"] == SERIAL]
    assert mine, "no alert was created for the CRITICAL prediction"
    ctx["alert_id"] = mine[0]["alert_id"]


def test_alert_acknowledge_flow(ctx, admin_headers):
    url = f"/api/alerts/{ctx['alert_id']}/acknowledge"
    r = client.put(url, headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ACKNOWLEDGED"
    assert client.put(url, headers=admin_headers).status_code == 409


def test_feedback_create(ctx):
    body = {"prediction_id": ctx["prediction_id"], "actual_outcome": "LOW",
            "outcome_source": "LAB_TEST", "submitted_by_role": "ADMIN"}
    r = client.post("/api/feedback", json=body)
    assert r.status_code in OK, r.text


def test_feedback_invalid_outcome_rejected(ctx):
    body = {"prediction_id": ctx["prediction_id"], "actual_outcome": "BAD",
            "outcome_source": "LAB_TEST", "submitted_by_role": "ADMIN"}
    assert client.post("/api/feedback", json=body).status_code == 422


def test_feedback_unknown_prediction_rejected():
    body = {"prediction_id": 999999, "actual_outcome": "LOW",
            "outcome_source": "LAB_TEST", "submitted_by_role": "ADMIN"}
    assert client.post("/api/feedback", json=body).status_code in (404, 409, 422)


def test_evaluate_saves_live_feedback_metrics():
    r = client.post("/api/model-performance/evaluate")
    assert r.status_code == 201, r.text
    saved = r.json()["saved"]
    assert saved, "no model had feedback to evaluate"
    for row in saved:
        assert row["evaluation_type"] == "LIVE_FEEDBACK"
        assert 0 <= float(row["accuracy"]) <= 1
        assert row["sample_count"] > 0


# ---------------- anomalies and recommendations ----------------
def test_anomaly_detect_ok(ctx, admin_headers):
    r = client.post("/api/anomalies/detect", json={"battery_id": ctx["battery_id"]}, headers=admin_headers)
    assert r.status_code in OK, r.text


def test_anomaly_detect_unknown_battery(admin_headers):
    assert client.post("/api/anomalies/detect", json={"battery_id": 999999}, headers=admin_headers).status_code == 404


def test_recommendations_generate_ok(ctx, admin_headers):
    r = client.post("/api/recommendations/generate", json={"battery_id": ctx["battery_id"]}, headers=admin_headers)
    assert r.status_code in OK, r.text


def test_recommendations_generate_unknown_battery(admin_headers):
    assert client.post("/api/recommendations/generate", json={"battery_id": 999999}, headers=admin_headers).status_code == 404


# ---------------- login ----------------
def test_login_success_and_me(admin_headers):
    r = client.get("/api/auth/me", headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json()["username"] == "admin1"
    assert client.get("/api/auth/admin-check", headers=admin_headers).status_code == 200


def test_login_wrong_password():
    r = client.post("/api/auth/login", json={"username": "admin1", "password": "wrong-password-xyz"})
    assert r.status_code == 401, r.text


def test_anomaly_detect_requires_login(ctx):
    r = client.post("/api/anomalies/detect", json={"battery_id": ctx["battery_id"]})
    assert r.status_code == 401, r.text


def test_recommendations_generate_requires_login(ctx):
    r = client.post("/api/recommendations/generate", json={"battery_id": ctx["battery_id"]})
    assert r.status_code == 401, r.text
