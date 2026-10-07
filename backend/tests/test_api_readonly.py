"""Backend tests, stage 1: read-only endpoints and failure cases. No data is changed.

Run from the backend folder:  python -m pytest tests -q
Needs PostgreSQL running with battery_db.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# One success case per read-only endpoint: must answer 200 with valid JSON.
GET_OK = [
    "/api/health",
    "/api/alerts",
    "/api/analytics/batteries",
    "/api/analytics/chemistry-comparison",
    "/api/analytics/dashboard",
    "/api/analytics/manufacturer-comparison",
    "/api/analytics/model-accuracy",
    "/api/analytics/open-alerts",
    "/api/anomalies",
    "/api/batteries",
    "/api/cfd-simulations",
    "/api/chemistries",
    "/api/digital-twins",
    "/api/feedback",
    "/api/manufacturers",
    "/api/model-performance",
    "/api/model-performance/live",
    "/api/models",
    "/api/predictions",
    "/api/recommendations",
]

# Failure cases: (method, path, expected status, optional JSON body).
FAILS = [
    ("GET", "/api/does-not-exist", 404, None),
    ("GET", "/api/alerts/999999", 404, None),
    ("GET", "/api/alerts?limit=0", 422, None),
    ("PUT", "/api/alerts/1/acknowledge", 401, None),
    ("GET", "/api/batteries/999999", 404, None),
    ("GET", "/api/batteries/abc", 422, None),
    ("GET", "/api/batteries/999999/aging", 404, None),
    ("GET", "/api/batteries/999999/aging/latest", 404, None),
    ("GET", "/api/batteries/999999/sensors", 404, None),
    ("GET", "/api/batteries/999999/twin", 404, None),
    ("GET", "/api/feedback/999999", 404, None),
    ("GET", "/api/feedback?limit=0", 422, None),
    ("GET", "/api/model-performance?limit=0", 422, None),
    ("GET", "/api/sensors/999999/readings", 404, None),
    ("GET", "/api/auth/me", 401, None),
    ("GET", "/api/auth/admin-check", 401, None),
    ("POST", "/api/auth/login", 422, None),
    ("POST", "/api/auth/login", 401, {"username": "nobody_xyz", "password": "wrong"}),
    ("POST", "/api/model-performance/evaluate", 404, {"model_id": 999999}),
]


@pytest.mark.parametrize("path", GET_OK)
def test_get_endpoint_ok(path):
    r = client.get(path)
    assert r.status_code == 200, r.text
    r.json()  # must be valid JSON


@pytest.mark.parametrize("method,path,status,body", FAILS)
def test_failure_cases(method, path, status, body):
    r = client.request(method, path, json=body)
    assert r.status_code == status, r.text
    data = r.json()
    # every error uses our consistent format
    assert data["error"]["code"] == status
    assert data["error"]["message"]
