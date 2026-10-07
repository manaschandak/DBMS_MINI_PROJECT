"""Backend entry point: predict_risk(features, risk_type)."""
from pathlib import Path

import joblib

_ART = Path(__file__).parent / "artifacts"
_cache: dict = {}


def _load(risk_type: str) -> dict:
    if risk_type not in _cache:
        path = _ART / f"{risk_type.lower()}_model.joblib"
        if not path.exists():
            raise FileNotFoundError(f"{path} missing - run `python -m ml.train` from the project root first")
        _cache[risk_type] = joblib.load(path)
    return _cache[risk_type]


def predict_risk(features: dict, risk_type: str) -> dict:
    """Return {"level": LOW|MEDIUM|HIGH|CRITICAL, "confidence": float 0-1}."""
    risk_type = str(risk_type).upper()
    if risk_type not in ("THERMAL", "HEALTH"):
        raise ValueError("risk_type must be 'THERMAL' or 'HEALTH'")
    art = _load(risk_type)
    missing = [f for f in art["features"] if features.get(f) is None]
    if missing:
        raise ValueError(f"missing features for {risk_type}: {missing}")
    import pandas as pd
    X = pd.DataFrame([{f: float(features[f]) for f in art["features"]}])
    model = art["model"]
    proba = model.predict_proba(X)[0]
    i = int(proba.argmax())
    return {"level": str(model.classes_[i]), "confidence": round(float(proba[i]), 4)}
