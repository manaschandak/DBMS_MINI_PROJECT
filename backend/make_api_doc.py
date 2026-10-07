"""Generate backend/API.md from the running app.

Run from the project root:  python backend/make_api_doc.py
The endpoint table comes from app.openapi(), so it always matches the code.
The role lists below are copied from the require_roles(...) calls in the routers;
update ROLES if those change.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from app.main import app  # noqa: E402

ROLES = {
    ("PUT", "/api/alerts/{alert_id}/acknowledge"): "ADMIN, BMS_ENGINEER, FLEET_OPERATOR, SERVICE_TECHNICIAN",
    ("POST", "/api/anomalies/detect"): "ADMIN, BMS_ENGINEER",
    ("POST", "/api/recommendations/generate"): "ADMIN, BMS_ENGINEER",
    ("GET", "/api/auth/admin-check"): "ADMIN",
    ("GET", "/api/auth/me"): "any logged-in user",
}

HEAD = """# Backend API

The endpoint table is generated from the running app (`app.openapi()`), so it matches the code.
Regenerate it with `python backend/make_api_doc.py` (from the project root).
Interactive version: start the server and open http://127.0.0.1:8000/docs

## Run the backend

```
cd backend
uvicorn app.main:app --reload
```

## Login

`POST /api/auth/login` with `{"username": ..., "password": ...}` returns an `access_token`.
Send it on protected calls as the header `Authorization: Bearer <token>`.
Roles: ADMIN, BMS_ENGINEER, FLEET_OPERATOR, SERVICE_TECHNICIAN, RESEARCHER.
Set a user's password with `python backend/set_password.py USERNAME` (from the project root).

## Errors

Every error has the same shape (`detail` is kept for older callers):

```
{"detail": "Battery not found", "error": {"code": 404, "message": "Battery not found"}}
```

Validation errors (422) also include `error.details`, a list of `{field, message}`.
Main codes: 401 not signed in or wrong login, 404 not found, 409 conflict (duplicate value,
row still in use, alert already acknowledged), 422 invalid input.

## Input limits

- List endpoints cap `limit`: alerts, feedback, predictions 200; model-performance 500;
  anomalies, recommendations 1000; aging and sensor readings 5000.
- `POST /api/readings` accepts at most 1000 readings per list (temperature, electrical, coolant)
  and rejects an empty batch.
- Text fields have maximum lengths in the request schemas.

## Predictions

`POST /api/predictions/risk` uses the trained model in `ml/` when it is available, otherwise fixed
threshold rules. The response field `model_kind` says which one answered
(`RANDOM_FOREST_SYNTHETIC` or `PLACEHOLDER_RULES`). The trained models use SYNTHETIC data only.
A reading of 60 C or more is always CRITICAL (safety rule in the router).

## Endpoints

| Method | Path | Login required | Query parameters | Request body |
|---|---|---|---|---|
"""

TAIL = """
## Known gaps

- Endpoints marked "no" in the Login column, including the create, update and delete endpoints
  for batteries, manufacturers, chemistries, sensors, readings, twins and CFD runs, can be called
  without logging in. This is fine for a local demo; protecting them is a design decision to make
  together with the frontend.
- `POST /api/models/retrain` is not built yet; it needs the training code in `ml/`.

## Tests

```
cd backend
python -m pytest tests -q --tb=short -rs
```

Tests run against battery_db. Rows they create are labelled TEST and deleted afterwards.
Tests that need a login are skipped unless the admin1 password is set for that terminal:
`$env:TEST_PASSWORD = "..."` (never commit it).
"""


def main():
    o = app.openapi()
    rows = []
    for path, methods in sorted(o["paths"].items()):
        for method, op in methods.items():
            query = ", ".join(p["name"] for p in op.get("parameters", []) if p["in"] == "query")
            body = ""
            rb = op.get("requestBody")
            if rb:
                schema = list(rb["content"].values())[0]["schema"]
                body = schema.get("$ref", "").split("/")[-1]
            key = (method.upper(), path)
            if key in ROLES:
                login = "yes: " + ROLES[key]
            elif op.get("security"):
                login = "yes"
            else:
                login = "no"
            rows.append(f"| {method.upper()} | `{path}` | {login} | {query or '-'} | {body or '-'} |")

    (HERE / "API.md").write_text(HEAD + "\n".join(rows) + "\n" + TAIL, encoding="utf-8")
    print("Wrote backend/API.md with", len(rows), "endpoints")


main()
