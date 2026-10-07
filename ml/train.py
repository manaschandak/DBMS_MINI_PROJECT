"""Train one risk model per risk_type on SYNTHETIC data and save it.

The labels come from threshold rules, so the model mostly reproduces those
rules. Metrics are on a held-out test set and are reported next to a plain
threshold-rule baseline. They are NOT real-world accuracy.
"""
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from .generate_data import (DATASET_NAME, FEATURES, LEVELS, generate_data,
                            _label_health, _label_thermal)

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ALGORITHM = "RandomForestClassifier"
HIGH = {"HIGH", "CRITICAL"}
_RULE = {"THERMAL": _label_thermal, "HEALTH": _label_health}


def _scores(y_true, y_pred) -> dict:
    y_pred = np.asarray(y_pred)
    is_high = y_true.isin(HIGH).values
    hits = sum(p in HIGH for p in y_pred[is_high])
    recall_hc = hits / max(int(is_high.sum()), 1)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro")), 4),
        "recall_high_critical": round(float(recall_hc), 4),
    }


def train_model(risk_type: str) -> dict:
    risk_type = str(risk_type).upper()  # accept "thermal" / "health"
    df = generate_data(risk_type)
    feats = FEATURES[risk_type]
    X_tr, X_te, y_tr, y_te = train_test_split(
        df[feats], df["label"], test_size=0.2, stratify=df["label"], random_state=42
    )
    model = RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=5,
        class_weight="balanced", random_state=42,
    ).fit(X_tr, y_tr)

    # Both are scored on the SAME held-out test set.
    model_scores = _scores(y_te, model.predict(X_te))
    rule = _RULE[risk_type]
    baseline = _scores(y_te, [rule(v) for v in X_te[feats[0]]])

    metrics = {
        "algorithm": ALGORITHM,
        "dataset_name": DATASET_NAME + " (SYNTHETIC)",
        "sample_count": int(len(df)),
        "test_sample_count": int(len(y_te)),
        **model_scores,
        "baseline_threshold_rule": baseline,
        "note": "Reproduces synthetic rule-based labels; not real-world accuracy.",
    }
    ARTIFACT_DIR.mkdir(exist_ok=True)
    path = ARTIFACT_DIR / f"{risk_type.lower()}_model.joblib"
    joblib.dump({"model": model, "features": feats, "levels": LEVELS, "meta": metrics}, path)
    return {"artifact_path": str(path), **metrics}


if __name__ == "__main__":
    out = {rt: train_model(rt) for rt in FEATURES}
    print(json.dumps(out, indent=2))