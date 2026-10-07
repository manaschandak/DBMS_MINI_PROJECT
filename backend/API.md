# Backend API

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
| GET | `/api/alerts` | no | status, priority_code, battery_id, limit, offset | - |
| GET | `/api/alerts/{alert_id}` | no | - | - |
| PUT | `/api/alerts/{alert_id}/acknowledge` | yes: ADMIN, BMS_ENGINEER, FLEET_OPERATOR, SERVICE_TECHNICIAN | - | - |
| GET | `/api/analytics/batteries` | no | - | - |
| GET | `/api/analytics/chemistry-comparison` | no | - | - |
| GET | `/api/analytics/dashboard` | no | - | - |
| GET | `/api/analytics/manufacturer-comparison` | no | - | - |
| GET | `/api/analytics/model-accuracy` | no | - | - |
| GET | `/api/analytics/open-alerts` | no | - | - |
| GET | `/api/anomalies` | no | battery_id, sensor_id, anomaly_type, cause, limit | - |
| POST | `/api/anomalies/detect` | yes: ADMIN, BMS_ENGINEER | - | DetectRequest |
| GET | `/api/auth/admin-check` | yes: ADMIN | - | - |
| POST | `/api/auth/login` | no | - | LoginRequest |
| GET | `/api/auth/me` | yes: any logged-in user | - | - |
| GET | `/api/batteries` | no | - | - |
| POST | `/api/batteries` | no | - | BatteryCreate |
| GET | `/api/batteries/{battery_id}` | no | - | - |
| PUT | `/api/batteries/{battery_id}` | no | - | BatteryCreate |
| DELETE | `/api/batteries/{battery_id}` | no | - | - |
| GET | `/api/batteries/{battery_id}/aging` | no | from, to, limit | - |
| POST | `/api/batteries/{battery_id}/aging` | no | - | AgingCreate |
| GET | `/api/batteries/{battery_id}/aging/latest` | no | - | - |
| GET | `/api/batteries/{battery_id}/sensors` | no | - | - |
| POST | `/api/batteries/{battery_id}/sensors` | no | - | SensorCreate |
| GET | `/api/batteries/{battery_id}/twin` | no | - | - |
| GET | `/api/cfd-simulations` | no | twin_id | - |
| POST | `/api/cfd-simulations` | no | - | CfdCreate |
| GET | `/api/chemistries` | no | - | - |
| POST | `/api/chemistries` | no | - | ChemistryCreate |
| GET | `/api/digital-twins` | no | - | - |
| POST | `/api/digital-twins` | no | - | TwinCreate |
| POST | `/api/feedback` | no | - | FeedbackCreate |
| GET | `/api/feedback` | no | prediction_id, battery_id, actual_outcome, limit, offset | - |
| GET | `/api/feedback/{feedback_id}` | no | - | - |
| GET | `/api/health` | no | - | - |
| GET | `/api/manufacturers` | no | - | - |
| POST | `/api/manufacturers` | no | - | ManufacturerCreate |
| PUT | `/api/manufacturers/{manufacturer_id}` | no | - | ManufacturerCreate |
| DELETE | `/api/manufacturers/{manufacturer_id}` | no | - | - |
| GET | `/api/model-performance` | no | model_id, evaluation_type, limit | - |
| POST | `/api/model-performance/evaluate` | no | - | - |
| GET | `/api/model-performance/live` | no | - | - |
| GET | `/api/models` | no | task_type, active_only | - |
| GET | `/api/predictions` | no | battery_id, risk_type, limit, offset | - |
| POST | `/api/predictions/risk` | no | - | PredictionRequest |
| POST | `/api/readings` | no | - | ReadingsBatch |
| GET | `/api/recommendations` | no | role, battery_id, limit | - |
| POST | `/api/recommendations/generate` | yes: ADMIN, BMS_ENGINEER | - | GenerateRequest |
| GET | `/api/sensors/{sensor_id}/readings` | no | from, to, limit | - |

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
