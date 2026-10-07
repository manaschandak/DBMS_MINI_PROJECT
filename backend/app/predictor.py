"""Risk prediction used by the backend.

Tries the trained Random Forest models in ml/ (trained on SYNTHETIC data).
If they are missing, falls back to fixed threshold rules and says so in MODEL_KIND.
The thresholds below are the same ones used to generate the synthetic training
data (ml/generate_data.py). They are a project SUGGESTION, not from the Word document.
"""
import sys
from pathlib import Path

# ml/ sits next to backend/, so the project root must be importable.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RULES_KIND = "PLACEHOLDER_RULES"
ML_KIND = "RANDOM_FOREST_SYNTHETIC"


def _load_ml():
    """Return ml.predict.predict_risk if both trained models work, else None."""
    try:
        from ml.predict import predict_risk as ml_predict
        ml_predict({"max_temp_c": 30.0}, "THERMAL")
        ml_predict({"capacity_pct": 95.0}, "HEALTH")
        return ml_predict
    except Exception as exc:
        print("[predictor] ML models not available, using fixed rules:", repr(exc))
        return None


_ml_predict = _load_ml()
MODEL_KIND = ML_KIND if _ml_predict is not None else RULES_KIND


def _rules_predict(features: dict, risk_type: str) -> dict:
    if risk_type == "THERMAL":
        value = features.get("max_temp_c")
        if value is None:
            raise ValueError("missing feature: max_temp_c")
        if value < 40:
            level = "LOW"
        elif value < 50:
            level = "MEDIUM"
        elif value < 60:
            level = "HIGH"
        else:
            level = "CRITICAL"
    elif risk_type == "HEALTH":
        value = features.get("capacity_pct")
        if value is None:
            raise ValueError("missing feature: capacity_pct")
        if value >= 90:
            level = "LOW"
        elif value >= 80:
            level = "MEDIUM"
        elif value >= 70:
            level = "HIGH"
        else:
            level = "CRITICAL"
    else:
        raise ValueError("Unknown risk_type: " + str(risk_type))

    # No confidence: fixed rules are not probabilistic, and inventing a number would mislead.
    return {"level": level, "confidence": None}


def predict_risk(features: dict, risk_type: str) -> dict:
    risk_type = str(risk_type).upper()
    if _ml_predict is not None:
        return _ml_predict(features, risk_type)
    return _rules_predict(features, risk_type)