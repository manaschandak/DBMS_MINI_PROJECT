"""Rule-based anomaly detection on temperature sensors, and listing of findings."""
from collections import defaultdict
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_anomalies as s
from app.database import get_db
from app.security import require_roles

router = APIRouter(prefix="/api", tags=["Anomalies"])

# ---------------------------------------------------------------------------
# THRESHOLDS: assumptions, change them here (nowhere else).
# ---------------------------------------------------------------------------
MAX_TEMP_C = {"NMC": 60.0, "LFP": 65.0, "NCA": 55.0}   # per chemistry
DEFAULT_MAX_TEMP_C = 60.0                               # chemistry not listed above
MIN_TEMP_C = -20.0
SPIKE_JUMP_C = 10.0          # jump between two consecutive readings
SPIKE_WINDOW_MIN = 5.0       # ...if they are at most this many minutes apart
NEIGHBOUR_WINDOW_SEC = 300   # a neighbour sensor reading counts if within 5 minutes
NEIGHBOUR_NORMAL_DIFF_C = 8.0  # neighbour differs from the flagged value by more than this = "stayed normal"
MAX_READINGS = 5000
# ---------------------------------------------------------------------------

AnomalyType = Literal["OUT_OF_RANGE", "SUDDEN_SPIKE", "FLATLINE", "DRIFT", "MODEL_OUTLIER"]
Cause = Literal["SENSOR_FAULT", "BATTERY_ISSUE", "UNDETERMINED"]


def decide_cause(by_sensor, sensor_id, when, value):
    """Poster rule: one sensor spikes while its neighbours stay normal = sensor fault."""
    compared = []
    for other_id, series in by_sensor.items():
        if other_id == sensor_id or not series:
            continue
        nearest = min(series, key=lambda r: abs((r[0] - when).total_seconds()))
        if abs((nearest[0] - when).total_seconds()) <= NEIGHBOUR_WINDOW_SEC:
            compared.append(nearest[1])
    if not compared:
        return "UNDETERMINED"   # no neighbour reading to compare with
    if all(abs(v - value) > NEIGHBOUR_NORMAL_DIFF_C for v in compared):
        return "SENSOR_FAULT"   # neighbours did not follow it
    return "BATTERY_ISSUE"      # neighbours moved too


@router.post("/anomalies/detect")
def detect(
    body: s.DetectRequest,
    user: dict = Depends(require_roles("ADMIN", "BMS_ENGINEER")),
    db: Session = Depends(get_db),
):
    battery = db.execute(
        text("SELECT b.battery_id, c.chemistry_code FROM battery b "
             "JOIN chemistry c ON c.chemistry_id = b.chemistry_id WHERE b.battery_id = :id"),
        {"id": body.battery_id},
    ).first()
    if battery is None:
        raise HTTPException(status_code=404, detail="Battery not found")

    where = ["s.battery_id = :bid", "s.sensor_type = 'TEMPERATURE'"]
    params = {"bid": body.battery_id, "limit": MAX_READINGS}
    if body.date_from is not None:
        where.append("t.recorded_at >= :d_from")
        params["d_from"] = body.date_from
    if body.date_to is not None:
        where.append("t.recorded_at <= :d_to")
        params["d_to"] = body.date_to
    try:
        readings = db.execute(
            text("SELECT t.sensor_id, t.recorded_at, t.temperature_c "
                 "FROM temperature_reading t JOIN sensor s ON s.sensor_id = t.sensor_id "
                 "WHERE " + " AND ".join(where) +
                 " ORDER BY t.sensor_id, t.recorded_at LIMIT :limit"),
            params,
        ).all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database error")

    by_sensor = defaultdict(list)
    for r in readings:
        by_sensor[r.sensor_id].append((r.recorded_at, float(r.temperature_c)))

    max_t = MAX_TEMP_C.get(battery.chemistry_code, DEFAULT_MAX_TEMP_C)
    findings = []
    for sensor_id, series in by_sensor.items():
        prev = None
        for when, value in series:
            if value > max_t or value < MIN_TEMP_C:
                excess = value - max_t if value > max_t else MIN_TEMP_C - value
                findings.append({"sensor_id": sensor_id, "at": when, "type": "OUT_OF_RANGE",
                                 "score": excess,
                                 "details": f"{value} C outside the allowed {MIN_TEMP_C} to {max_t} C"})
            if prev is not None:
                minutes = (when - prev[0]).total_seconds() / 60
                jump = abs(value - prev[1])
                if minutes <= SPIKE_WINDOW_MIN and jump >= SPIKE_JUMP_C:
                    findings.append({"sensor_id": sensor_id, "at": when, "type": "SUDDEN_SPIKE",
                                     "score": jump,
                                     "details": f"Changed {jump:.1f} C in {minutes:.1f} min ({prev[1]} to {value})"})
            prev = (when, value)

    saved = 0
    results = []
    try:
        for f in findings:
            value = next(v for (t, v) in by_sensor[f["sensor_id"]] if t == f["at"])
            cause = decide_cause(by_sensor, f["sensor_id"], f["at"], value)
            score = round(min(abs(f["score"]), 999.999), 3)
            res = db.execute(
                text("INSERT INTO sensor_anomaly (sensor_id, detected_at, anomaly_type, cause, "
                     "detection_method, anomaly_score, details) "
                     "VALUES (:sid, :at, :type, :cause, 'RULE', :score, :details) "
                     "ON CONFLICT (sensor_id, detected_at, anomaly_type) DO NOTHING"),
                {"sid": f["sensor_id"], "at": f["at"], "type": f["type"],
                 "cause": cause, "score": score, "details": f["details"]},
            )
            saved += res.rowcount
            results.append({"sensor_id": f["sensor_id"], "detected_at": f["at"],
                            "anomaly_type": f["type"], "cause": cause, "anomaly_score": score})
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error. Nothing was saved.")

    return {"battery_id": body.battery_id, "chemistry": battery.chemistry_code,
            "max_temp_c_used": max_t, "readings_checked": len(readings),
            "found": len(findings), "newly_saved": saved, "findings": results}


@router.get("/anomalies", response_model=list[s.AnomalyOut])
def list_anomalies(
    battery_id: Optional[int] = Query(None, gt=0),
    sensor_id: Optional[int] = Query(None, gt=0),
    anomaly_type: Optional[AnomalyType] = None,
    cause: Optional[Cause] = None,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    where, params = [], {"limit": limit}
    for column, key, value in (("s.battery_id", "bid", battery_id), ("a.sensor_id", "sid", sensor_id),
                               ("a.anomaly_type", "atype", anomaly_type), ("a.cause", "cause", cause)):
        if value is not None:
            where.append(f"{column} = :{key}")
            params[key] = value
    sql = ("SELECT a.anomaly_id, a.sensor_id, s.battery_id, s.location, a.detected_at, "
           "a.anomaly_type, a.cause, a.detection_method, a.anomaly_score, a.details "
           "FROM sensor_anomaly a JOIN sensor s ON s.sensor_id = a.sensor_id")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY a.detected_at DESC LIMIT :limit"
    try:
        return db.execute(text(sql), params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database error")