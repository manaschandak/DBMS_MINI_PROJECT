"""Alerts: list, view, acknowledge."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_alerts as a
from app.database import get_db
from app.security import require_roles

router = APIRouter(prefix="/api", tags=["Alerts"])

# Path from an alert to its battery: alert > risk_assessment > prediction_result > battery
ALERT_SELECT = (
    "SELECT a.alert_id, b.battery_id, b.serial_number, ap.priority_code, "
    "ap.severity_level, ra.final_risk_level, a.message, a.status, "
    "a.created_at, a.acknowledged_at "
    "FROM alert a "
    "JOIN alert_priority ap ON ap.alert_priority_id = a.alert_priority_id "
    "JOIN risk_assessment ra ON ra.assessment_id = a.assessment_id "
    "JOIN prediction_result pr ON pr.prediction_id = ra.prediction_id "
    "JOIN battery b ON b.battery_id = pr.battery_id"
)


@router.get("/alerts", response_model=list[a.AlertOut])
def list_alerts(
    status: Optional[Literal["OPEN", "ACKNOWLEDGED", "RESOLVED"]] = None,
    battery_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    where, params = [], {"limit": limit}
    if status is not None:
        where.append("a.status = :status")
        params["status"] = status
    if battery_id is not None:
        where.append("b.battery_id = :bid")
        params["bid"] = battery_id
    sql = ALERT_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ap.severity_level DESC, a.created_at DESC LIMIT :limit"
    try:
        return db.execute(text(sql), params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database error")


@router.get("/alerts/{alert_id}", response_model=a.AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(ALERT_SELECT + " WHERE a.alert_id = :id"),
                     {"id": alert_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return row


@router.put("/alerts/{alert_id}/acknowledge", response_model=a.AlertOut)
def acknowledge_alert(
    alert_id: int,
    user: dict = Depends(require_roles("ADMIN", "BMS_ENGINEER", "FLEET_OPERATOR", "SERVICE_TECHNICIAN")),
    db: Session = Depends(get_db),
):
    """Only an OPEN alert can be acknowledged. Status and time are set together,
    which is what the database rule chk_alert_ack_matches_status requires."""
    try:
        changed = db.execute(
            text("UPDATE alert SET status = 'ACKNOWLEDGED', acknowledged_at = now() "
                 "WHERE alert_id = :id AND status = 'OPEN' RETURNING alert_id"),
            {"id": alert_id},
        ).first()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")

    if changed is None:
        exists = db.execute(text("SELECT status FROM alert WHERE alert_id = :id"),
                            {"id": alert_id}).first()
        if exists is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        raise HTTPException(status_code=409,
                            detail=f"Alert is already {exists.status.lower()}")
    return db.execute(text(ALERT_SELECT + " WHERE a.alert_id = :id"),
                      {"id": alert_id}).mappings().one()