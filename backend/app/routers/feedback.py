"""Feedback: the actual outcome recorded against an earlier prediction."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas_feedback import FeedbackCreate, FeedbackOut, Outcome

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Fixed SQL text only; every value is passed as a bound parameter.
SELECT_SQL = """
    SELECT f.feedback_id, f.prediction_id, b.serial_number, m.risk_type,
           p.predicted_label, f.actual_outcome,
           (p.predicted_label = f.actual_outcome) AS matches_prediction,
           f.outcome_source, f.submitted_by_role, f.observed_at, f.notes, f.created_at
    FROM feedback f
    JOIN prediction_result p ON f.prediction_id = p.prediction_id
    JOIN battery b           ON p.battery_id = b.battery_id
    JOIN ai_model m          ON p.model_id = m.model_id
"""


def _sqlstate(exc):
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


@router.post("", response_model=FeedbackOut, status_code=201)
def create_feedback(body: FeedbackCreate, db: Session = Depends(get_db)):
    """Record the actual outcome for a prediction."""
    data = body.model_dump()
    if data["observed_at"] is None:
        data["observed_at"] = datetime.now(timezone.utc)
    try:
        new_id = db.execute(
            text(
                """
                INSERT INTO feedback
                    (prediction_id, actual_outcome, outcome_source,
                     submitted_by_role, observed_at, notes)
                VALUES
                    (:prediction_id, :actual_outcome, :outcome_source,
                     :submitted_by_role, :observed_at, :notes)
                RETURNING feedback_id
                """
            ),
            data,
        ).scalar_one()
        db.commit()
        row = db.execute(
            text(SELECT_SQL + " WHERE f.feedback_id = :id"), {"id": new_id}
        ).mappings().first()
    except IntegrityError as exc:
        db.rollback()
        code = _sqlstate(exc)
        if code == "23503":
            raise HTTPException(status_code=422, detail="prediction_id does not exist")
        if code in ("23514", "23502"):
            raise HTTPException(status_code=422, detail="A value was rejected by a database rule")
        raise HTTPException(status_code=409, detail="Conflict with existing data")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return dict(row)


@router.get("", response_model=list[FeedbackOut])
def list_feedback(
    prediction_id: Optional[int] = Query(None, ge=1),
    battery_id: Optional[int] = Query(None, ge=1),
    actual_outcome: Optional[Outcome] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List feedback, newest first. All filters are optional."""
    conditions = []
    params = {"limit": limit, "offset": offset}
    if prediction_id is not None:
        conditions.append("f.prediction_id = :prediction_id")
        params["prediction_id"] = prediction_id
    if battery_id is not None:
        conditions.append("b.battery_id = :battery_id")
        params["battery_id"] = battery_id
    if actual_outcome:
        conditions.append("f.actual_outcome = :actual_outcome")
        params["actual_outcome"] = actual_outcome
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    try:
        rows = db.execute(
            text(
                SELECT_SQL
                + where
                + " ORDER BY f.created_at DESC, f.feedback_id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return [dict(row) for row in rows]


@router.get("/{feedback_id}", response_model=FeedbackOut)
def get_feedback(feedback_id: int, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text(SELECT_SQL + " WHERE f.feedback_id = :id"), {"id": feedback_id}
        ).mappings().first()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    if row is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return dict(row)