"""Risk predictions: gather features, predict, save prediction + assessment, recommend."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.predictor import MODEL_KIND, predict_risk
from app.schemas_predictions import (
    PredictionCreated,
    PredictionOut,
    PredictionRequest,
    RiskType,
)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# SUGGESTION: a reading at or above this forces CRITICAL. Confirm or change per chemistry.
HARD_LIMIT_TEMP_C = 60.0

RECOMMENDATIONS = {
    "THERMAL": {
        "CRITICAL": {
            "FLEET_OPERATOR": "Take the vehicle out of service until it has been inspected.",
            "SERVICE_TECHNICIAN": "Inspect this battery and its coolant loop immediately.",
            "BMS_ENGINEER": "Review the recent temperature data and check the cooling system and thermal limits.",
        },
        "HIGH": {
            "FLEET_OPERATOR": "Reduce charging and load on this vehicle and book an inspection soon.",
            "SERVICE_TECHNICIAN": "Inspect this battery soon and check coolant flow and temperature sensors.",
            "BMS_ENGINEER": "Check the temperature trend and consider lowering the charge and discharge limits.",
        },
    },
    "HEALTH": {
        "CRITICAL": {
            "FLEET_OPERATOR": "Plan to replace or service this battery; expect reduced range and reliability.",
            "SERVICE_TECHNICIAN": "Test capacity and internal resistance and prepare a replacement.",
            "BMS_ENGINEER": "Review the aging history and recalibrate the state-of-health estimate.",
        },
        "HIGH": {
            "FLEET_OPERATOR": "Schedule a battery health check at the next service.",
            "SERVICE_TECHNICIAN": "Measure capacity and internal resistance at the next visit.",
            "BMS_ENGINEER": "Compare this battery's aging trend with others of the same chemistry.",
        },
    },
}

# Fixed SQL text only; every value is passed as a bound parameter.
LIST_SQL = """
    SELECT p.prediction_id, b.battery_id, b.serial_number, m.risk_type, m.model_name,
           p.predicted_label, p.confidence, ra.final_risk_level, ra.rule_override,
           p.predicted_at, p.notes
    FROM prediction_result p
    JOIN battery b  ON p.battery_id = b.battery_id
    JOIN ai_model m ON p.model_id = m.model_id
    LEFT JOIN risk_assessment ra ON ra.prediction_id = p.prediction_id
"""


def _float(value):
    return float(value) if value is not None else None


def _gather_features(db: Session, battery_id: int):
    battery = db.execute(
        text(
            "SELECT b.battery_id, b.serial_number, c.chemistry_code "
            "FROM battery b JOIN chemistry c ON b.chemistry_id = c.chemistry_id "
            "WHERE b.battery_id = :id"
        ),
        {"id": battery_id},
    ).mappings().first()
    if battery is None:
        raise HTTPException(status_code=404, detail="Battery not found")

    max_temp = db.execute(
        text(
            """
            SELECT max(lt.temperature_c)
            FROM sensor s
            CROSS JOIN LATERAL (
                SELECT tr.temperature_c FROM temperature_reading tr
                WHERE tr.sensor_id = s.sensor_id
                ORDER BY tr.recorded_at DESC LIMIT 1) lt
            WHERE s.battery_id = :id
            """
        ),
        {"id": battery_id},
    ).scalar()

    aging = db.execute(
        text(
            """
            SELECT ar.cycle_count, ar.internal_resistance_mohm,
                   CASE WHEN b.nominal_capacity_ah > 0
                        THEN ar.capacity_ah / b.nominal_capacity_ah * 100 END AS capacity_pct
            FROM aging_record ar
            JOIN battery b ON ar.battery_id = b.battery_id
            WHERE ar.battery_id = :id
            ORDER BY ar.measured_at DESC LIMIT 1
            """
        ),
        {"id": battery_id},
    ).mappings().first()

    features = {
        "chemistry_code": battery["chemistry_code"],
        "max_temp_c": _float(max_temp),
        "cycle_count": aging["cycle_count"] if aging else None,
        "internal_resistance_mohm": _float(aging["internal_resistance_mohm"]) if aging else None,
        "capacity_pct": _float(aging["capacity_pct"]) if aging else None,
    }
    return battery, features


@router.post("/risk", response_model=PredictionCreated, status_code=201)
def create_risk_prediction(body: PredictionRequest, db: Session = Depends(get_db)):
    """Predict risk for one battery and save prediction, assessment, alert (trigger) and advice."""
    try:
        battery, features = _gather_features(db, body.battery_id)

        if body.risk_type == "THERMAL" and features["max_temp_c"] is None:
            raise HTTPException(status_code=422, detail="No temperature readings for this battery")
        if body.risk_type == "HEALTH" and features["capacity_pct"] is None:
            raise HTTPException(status_code=422, detail="No aging record for this battery")

        # Prefer an active model; otherwise use the newest row for this risk type.
        model = db.execute(
            text(
                "SELECT model_id, model_name FROM ai_model "
                "WHERE risk_type = :rt ORDER BY is_active DESC, model_id DESC LIMIT 1"
            ),
            {"rt": body.risk_type},
        ).mappings().first()
        if model is None:
            raise HTTPException(status_code=409, detail="No model registered for this risk type")

        result = predict_risk(features, body.risk_type)
        predicted = result["level"]
        final, override = predicted, False
        if (
            body.risk_type == "THERMAL"
            and features["max_temp_c"] >= HARD_LIMIT_TEMP_C
            and predicted != "CRITICAL"
        ):
            final, override = "CRITICAL", True

        note = "PLACEHOLDER RULES (not a trained model)"
        if body.notes:
            note += " | " + body.notes

        pred = db.execute(
            text(
                "INSERT INTO prediction_result "
                "(model_id, battery_id, predicted_label, confidence, notes) "
                "VALUES (:model_id, :battery_id, :label, :confidence, :notes) "
                "RETURNING prediction_id, predicted_at"
            ),
            {
                "model_id": model["model_id"],
                "battery_id": body.battery_id,
                "label": predicted,
                "confidence": result.get("confidence"),
                "notes": note,
            },
        ).mappings().first()

        assessment_id = db.execute(
            text(
                "INSERT INTO risk_assessment (prediction_id, final_risk_level, rule_override) "
                "VALUES (:pid, :level, :override) RETURNING assessment_id"
            ),
            {"pid": pred["prediction_id"], "level": final, "override": override},
        ).scalar_one()

        recs = RECOMMENDATIONS.get(body.risk_type, {}).get(final, {})
        for role, advice in recs.items():
            db.execute(
                text(
                    "INSERT INTO recommendation (target_role, assessment_id, recommendation_text) "
                    "VALUES (:role, :aid, :txt)"
                ),
                {"role": role, "aid": assessment_id, "txt": advice},
            )
        db.commit()

        alert_id = db.execute(
            text("SELECT alert_id FROM alert WHERE assessment_id = :aid ORDER BY alert_id LIMIT 1"),
            {"aid": assessment_id},
        ).scalar()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=422, detail="A value was rejected by a database rule")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "prediction_id": pred["prediction_id"],
        "assessment_id": assessment_id,
        "battery_id": battery["battery_id"],
        "serial_number": battery["serial_number"],
        "risk_type": body.risk_type,
        "model_name": model["model_name"],
        "model_kind": MODEL_KIND,
        "predicted_label": predicted,
        "confidence": result.get("confidence"),
        "final_risk_level": final,
        "rule_override": override,
        "alert_id": alert_id,
        "recommendations_created": len(recs),
        "predicted_at": pred["predicted_at"],
        "notes": note,
    }


@router.get("", response_model=list[PredictionOut])
def list_predictions(
    battery_id: Optional[int] = Query(None, ge=1),
    risk_type: Optional[RiskType] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List predictions with their final assessment, newest first."""
    conditions = []
    params = {"limit": limit, "offset": offset}
    if battery_id is not None:
        conditions.append("b.battery_id = :battery_id")
        params["battery_id"] = battery_id
    if risk_type:
        conditions.append("m.risk_type = :risk_type")
        params["risk_type"] = risk_type
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    try:
        rows = db.execute(
            text(
                LIST_SQL
                + where
                + " ORDER BY p.predicted_at DESC, p.prediction_id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    return [dict(r) for r in rows]