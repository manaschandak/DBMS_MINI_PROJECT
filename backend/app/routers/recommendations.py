"""Recommendations: list them, and generate them from risk levels and anomalies."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_recommendations as r
from app.database import get_db
from app.security import require_roles

router = APIRouter(prefix="/api", tags=["Recommendations"])

# ---------------------------------------------------------------------------
# ADVICE TABLES: wording is an assumption, edit it here (nowhere else).
# ---------------------------------------------------------------------------
RISK_ADVICE = {
    "CRITICAL": {
        "FLEET_OPERATOR": "Take the vehicle out of service until the battery has been inspected.",
        "SERVICE_TECHNICIAN": "Inspect the battery pack and coolant loop immediately.",
        "BMS_ENGINEER": "Reduce charge and discharge limits now and review the cooling performance.",
        "MANUFACTURER": "Review this unit's recent history for a possible design or batch issue.",
    },
    "HIGH": {
        "FLEET_OPERATOR": "Limit fast charging and heavy loads and schedule an inspection soon.",
        "SERVICE_TECHNICIAN": "Schedule a thermal inspection and check the coolant flow.",
        "BMS_ENGINEER": "Check the temperature trend and the alert thresholds for this battery.",
    },
    "MEDIUM": {
        "FLEET_OPERATOR": "Keep monitoring this battery and review it at the next scheduled check.",
        "BMS_ENGINEER": "Watch the temperature and resistance trend for this battery.",
    },
    "LOW": {},   # nothing to recommend
}
ANOMALY_ADVICE = {
    "SENSOR_FAULT": {
        "SERVICE_TECHNICIAN": "Inspect or replace the sensor. Its readings disagree with its neighbours.",
        "BMS_ENGINEER": "Check this temperature sensor. The reading may be faulty, not the battery.",
    },
    "BATTERY_ISSUE": {
        "BMS_ENGINEER": "Several sensors agree on an abnormal temperature. Review the battery's thermal behaviour.",
        "FLEET_OPERATOR": "Reduce load on this vehicle until the abnormal temperature is checked.",
        "SERVICE_TECHNICIAN": "Inspect the battery pack and coolant loop for the cause of the abnormal temperature.",
    },
    "UNDETERMINED": {
        "BMS_ENGINEER": "An abnormal reading was found but the cause is unclear. Compare it with other sensors.",
    },
}
LATEST_ASSESSMENTS = 4     # how many recent risk assessments to use per battery
LATEST_ANOMALIES = 20      # how many recent anomalies to use per battery
# ---------------------------------------------------------------------------

Role = Literal["BMS_ENGINEER", "FLEET_OPERATOR", "MANUFACTURER", "SERVICE_TECHNICIAN"]

# battery_id comes from the risk path or the anomaly path, whichever the row uses.
LIST_SELECT = (
    "SELECT r.recommendation_id, r.target_role, b.battery_id, b.serial_number, "
    "CASE WHEN r.assessment_id IS NOT NULL THEN 'RISK' ELSE 'ANOMALY' END AS source_type, "
    "r.assessment_id, r.anomaly_id, ra.final_risk_level AS risk_level, "
    "an.anomaly_type, an.cause, r.recommendation_text, r.created_at "
    "FROM recommendation r "
    "LEFT JOIN risk_assessment ra ON ra.assessment_id = r.assessment_id "
    "LEFT JOIN prediction_result pr ON pr.prediction_id = ra.prediction_id "
    "LEFT JOIN sensor_anomaly an ON an.anomaly_id = r.anomaly_id "
    "LEFT JOIN sensor s ON s.sensor_id = an.sensor_id "
    "JOIN battery b ON b.battery_id = COALESCE(pr.battery_id, s.battery_id)"
)

# Insert only if this role has no recommendation yet for this source.
INSERT_ONCE = (
    "INSERT INTO recommendation (target_role, assessment_id, anomaly_id, recommendation_text) "
    "SELECT CAST(:role AS varchar), CAST(:aid AS integer), CAST(:nid AS integer), CAST(:txt AS text) "
    "WHERE NOT EXISTS (SELECT 1 FROM recommendation "
    "WHERE target_role = CAST(:role AS varchar) "
    "AND assessment_id IS NOT DISTINCT FROM CAST(:aid AS integer) "
    "AND anomaly_id IS NOT DISTINCT FROM CAST(:nid AS integer))"
)


@router.get("/recommendations", response_model=list[r.RecommendationOut])
def list_recommendations(
    role: Optional[Role] = None,
    battery_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    where, params = [], {"limit": limit}
    if role is not None:
        where.append("r.target_role = :role")
        params["role"] = role
    if battery_id is not None:
        where.append("b.battery_id = :bid")
        params["bid"] = battery_id
    sql = LIST_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.created_at DESC, r.recommendation_id DESC LIMIT :limit"
    try:
        return db.execute(text(sql), params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database error")


@router.post("/recommendations/generate")
def generate(
    body: r.GenerateRequest,
    user: dict = Depends(require_roles("ADMIN", "BMS_ENGINEER")),
    db: Session = Depends(get_db),
):
    if db.execute(text("SELECT 1 FROM battery WHERE battery_id = :id"),
                  {"id": body.battery_id}).first() is None:
        raise HTTPException(status_code=404, detail="Battery not found")

    created, existing, unknown_levels = 0, 0, set()
    try:
        assessments = db.execute(
            text("SELECT ra.assessment_id, ra.final_risk_level "
                 "FROM risk_assessment ra "
                 "JOIN prediction_result pr ON pr.prediction_id = ra.prediction_id "
                 "WHERE pr.battery_id = :bid ORDER BY ra.assessment_id DESC LIMIT :n"),
            {"bid": body.battery_id, "n": LATEST_ASSESSMENTS},
        ).all()
        anomalies = db.execute(
            text("SELECT an.anomaly_id, an.cause FROM sensor_anomaly an "
                 "JOIN sensor s ON s.sensor_id = an.sensor_id "
                 "WHERE s.battery_id = :bid ORDER BY an.anomaly_id DESC LIMIT :n"),
            {"bid": body.battery_id, "n": LATEST_ANOMALIES},
        ).all()

        for a in assessments:
            level = str(a.final_risk_level).upper()
            if level not in RISK_ADVICE:
                unknown_levels.add(str(a.final_risk_level))
                continue
            for role, advice in RISK_ADVICE[level].items():
                res = db.execute(text(INSERT_ONCE),
                                 {"role": role, "aid": a.assessment_id, "nid": None, "txt": advice})
                created += res.rowcount
                existing += 1 - res.rowcount

        for an in anomalies:
            for role, advice in ANOMALY_ADVICE.get(an.cause, {}).items():
                res = db.execute(text(INSERT_ONCE),
                                 {"role": role, "aid": None, "nid": an.anomaly_id, "txt": advice})
                created += res.rowcount
                existing += 1 - res.rowcount
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error. Nothing was saved.")

    return {"battery_id": body.battery_id,
            "assessments_checked": len(assessments), "anomalies_checked": len(anomalies),
            "created": created, "already_existed": existing,
            "unknown_risk_levels_skipped": sorted(unknown_levels)}