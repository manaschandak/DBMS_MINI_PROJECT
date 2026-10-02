"""AI models and their performance.

GET  /api/models                       list models
GET  /api/model-performance            stored metrics (TEST_SET and LIVE_FEEDBACK rows)
GET  /api/model-performance/live       current accuracy per model, from the v_live_accuracy view
POST /api/model-performance/evaluate   compute metrics from feedback and store them
"""
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.metrics import compute_metrics
from app.schemas_models import (
    EvaluateRequest,
    EvaluateResult,
    LiveAccuracyOut,
    ModelOut,
    PerformanceOut,
)

router = APIRouter(prefix="/api", tags=["models"])

# Fixed SQL text only; every value is passed as a bound parameter.
MODELS_SQL = """
    SELECT model_id, model_name, version, task_type, algorithm, risk_type,
           trained_at, is_active, notes
    FROM ai_model
"""

PERFORMANCE_SQL = """
    SELECT mp.performance_id, mp.model_id, m.model_name, m.version, mp.evaluation_type,
           mp.sample_count, mp.accuracy, mp.macro_f1, mp.recall_high_critical,
           mp.evaluated_at, mp.notes
    FROM model_performance mp
    JOIN ai_model m ON mp.model_id = m.model_id
"""

LIVE_SQL = """
    SELECT model_id, model_name, risk_type, feedback_count, exact_matches, accuracy, underestimated
    FROM v_live_accuracy
    ORDER BY model_name
"""

# Each feedback row is one case: what the model predicted vs what really happened.
FEEDBACK_PAIRS_SQL = """
    SELECT p.predicted_label, f.actual_outcome
    FROM feedback f
    JOIN prediction_result p ON f.prediction_id = p.prediction_id
    WHERE p.model_id = :model_id
    ORDER BY f.feedback_id
"""

INSERT_PERFORMANCE_SQL = """
    INSERT INTO model_performance
        (model_id, evaluation_type, sample_count, accuracy, macro_f1, recall_high_critical, notes)
    VALUES
        (:model_id, 'LIVE_FEEDBACK', :sample_count, :accuracy, :macro_f1, :recall_high_critical, :notes)
    RETURNING performance_id
"""

EVALUATION_NOTES = (
    "Computed from feedback: each feedback row is one case, comparing the model's raw "
    "predicted_label with the actual outcome. recall_high_critical = share of cases with actual "
    "HIGH or CRITICAL that the model predicted as HIGH or CRITICAL."
)


def _database_error(db: Session, exc: Exception):
    db.rollback()
    raise HTTPException(status_code=500, detail="Database error") from exc


@router.get("/models", response_model=List[ModelOut])
def list_models(
    task_type: Optional[Literal["RISK_CLASSIFICATION", "ANOMALY_DETECTION", "DEGRADATION_REGRESSION"]] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    clauses, params = [], {}
    if task_type is not None:
        clauses.append("task_type = :task_type")
        params["task_type"] = task_type
    if active_only:
        clauses.append("is_active")
    sql = MODELS_SQL
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY model_name, version"
    try:
        rows = db.execute(text(sql), params).mappings().all()
    except SQLAlchemyError as exc:
        _database_error(db, exc)
    return [dict(r) for r in rows]


@router.get("/model-performance", response_model=List[PerformanceOut])
def list_performance(
    model_id: Optional[int] = Query(default=None, ge=1),
    evaluation_type: Optional[Literal["TEST_SET", "LIVE_FEEDBACK"]] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    clauses, params = [], {"limit": limit}
    if model_id is not None:
        clauses.append("mp.model_id = :model_id")
        params["model_id"] = model_id
    if evaluation_type is not None:
        clauses.append("mp.evaluation_type = :evaluation_type")
        params["evaluation_type"] = evaluation_type
    sql = PERFORMANCE_SQL
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY mp.evaluated_at DESC, mp.performance_id DESC LIMIT :limit"
    try:
        rows = db.execute(text(sql), params).mappings().all()
    except SQLAlchemyError as exc:
        _database_error(db, exc)
    return [dict(r) for r in rows]


@router.get("/model-performance/live", response_model=List[LiveAccuracyOut])
def live_accuracy(db: Session = Depends(get_db)):
    """Current numbers calculated on the fly from feedback. Nothing is stored."""
    try:
        rows = db.execute(text(LIVE_SQL)).mappings().all()
    except SQLAlchemyError as exc:
        _database_error(db, exc)
    return [dict(r) for r in rows]


@router.post("/model-performance/evaluate", response_model=EvaluateResult, status_code=201)
def evaluate_models(body: Optional[EvaluateRequest] = None, db: Session = Depends(get_db)):
    """Measure models against feedback and store one LIVE_FEEDBACK row per model.

    Calling it again adds new rows, which is how performance over time is tracked.
    """
    try:
        if body is not None and body.model_id is not None:
            found = db.execute(
                text("SELECT model_id FROM ai_model WHERE model_id = :model_id"),
                {"model_id": body.model_id},
            ).first()
            if found is None:
                raise HTTPException(status_code=404, detail="Model not found")
            model_ids = [body.model_id]
        else:
            model_ids = [r[0] for r in db.execute(text("SELECT model_id FROM ai_model ORDER BY model_id")).all()]

        saved, skipped = [], []
        for model_id in model_ids:
            pairs = db.execute(text(FEEDBACK_PAIRS_SQL), {"model_id": model_id}).all()
            if not pairs:
                skipped.append(model_id)
                continue
            predicted = [row[0] for row in pairs]
            actual = [row[1] for row in pairs]
            metrics = compute_metrics(actual, predicted)
            new_id = db.execute(
                text(INSERT_PERFORMANCE_SQL),
                {"model_id": model_id, **metrics, "notes": EVALUATION_NOTES},
            ).scalar()
            row = db.execute(
                text(PERFORMANCE_SQL + " WHERE mp.performance_id = :pid"), {"pid": new_id}
            ).mappings().one()
            saved.append(dict(row))

        db.commit()
        return {"saved": saved, "skipped_model_ids": skipped}
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        _database_error(db, exc)
