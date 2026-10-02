"""Alerts: list by priority and acknowledge."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas_alerts import AlertOut, PriorityCode

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Fixed SQL text only; every value is passed as a bound parameter.
SELECT_SQL = """
    SELECT a.alert_id, ap.priority_code, ap.severity_level,
           b.battery_id, b.serial_number, m.risk_type, ra.final_risk_level,
           a.message, a.status, a.created_at, a.acknowledged_at
    FROM alert a
    JOIN alert_priority ap    ON a.alert_priority_id = ap.alert_priority_id
    JOIN risk_assessment ra   ON a.assessment_id = ra.assessment_id
    JOIN prediction_result pr ON ra.prediction_id = pr.prediction_id
    JOIN battery b            ON pr.battery_id = b.battery_id
    JOIN ai_model m           ON pr.model_id = m.model_id
"""


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: Optional[str] = Query(None, pattern="^[A-Z_]{3,20}$"),
    priority_code: Optional[PriorityCode] = None,
    battery_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List alerts, most severe first, then newest. All filters are optional."""
    conditions = []
    params = {"limit": limit, "offset": offset}
    if status:
        conditions.append("a.status = :status")
        params["status"] = status
    if priority_code:
        conditions.append("ap.priority_code = :priority_code")
        params["priority_code"] = priority_code
    if battery_id is not None:
        conditions.append("b.battery_id = :battery_id")
        params["battery_id"] = battery_id
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    try:
        rows = db.execute(
            text(
                SELECT_SQL
                + where
                + " ORDER BY ap.severity_level DESC, a.created_at DESC, a.alert_id DESC"
                + " LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return [dict(row) for row in rows]


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text(SELECT_SQL + " WHERE a.alert_id = :id"), {"id": alert_id}
        ).mappings().first()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return dict(row)


@router.put("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an OPEN alert as ACKNOWLEDGED. One atomic UPDATE, so it cannot be done twice."""
    try:
        updated = db.execute(
            text(
                "UPDATE alert SET status = 'ACKNOWLEDGED', acknowledged_at = now() "
                "WHERE alert_id = :id AND status = 'OPEN' RETURNING alert_id"
            ),
            {"id": alert_id},
        ).first()
        if updated is None:
            exists = db.execute(
                text("SELECT 1 FROM alert WHERE alert_id = :id"), {"id": alert_id}
            ).first()
            db.rollback()
            if exists is None:
                raise HTTPException(status_code=404, detail="Alert not found")
            raise HTTPException(status_code=409, detail="Alert is not open (already acknowledged)")
        db.commit()
        row = db.execute(
            text(SELECT_SQL + " WHERE a.alert_id = :id"), {"id": alert_id}
        ).mappings().first()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return dict(row)