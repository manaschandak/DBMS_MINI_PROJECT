"""Train one risk model per risk_type on SYNTHETIC data and save it."""
import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from generate_data import DATASET_NAME, FEATURES, LEVELS, generate_data

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ALGORITHM = "RandomForestClassifier"


def train_model(risk_type: str) -> dict:
    df = generate_data(risk_type)
    feats = FEATURES[risk_type]
    X_tr, X_te, y_tr, y_te = train_test_split(
        df[feats], df["label"], test_size=0.2, stratify=df["label"], random_state=42
    )
    model = RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=5,
        class_weight="balanced", random_state=42,
    ).fit(X_tr, y_tr)

    pred = model.predict(X_te)  # held-out test set only
    high = {"HIGH", "CRITICAL"}
    is_high = y_te.isin(high)
    recall_hc = float(sum(p in high for p in pred[is_high.values]) / max(is_high.sum(), 1))

    metrics = {
        "algorithm": ALGORITHM,
        "dataset_name": DATASET_NAME + " (SYNTHETIC)",
        "sample_count": int(len(df)),
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
        "recall_high_critical": round(recall_hc, 4),
    }
    ARTIFACT_DIR.mkdir(exist_ok=True)
    path = ARTIFACT_DIR / f"{risk_type.lower()}_model.joblib"
    joblib.dump({"model": model, "features": feats, "levels": LEVELS, "meta": metrics}, path)
    return {"artifact_path": str(path), **metrics}


if __name__ == "__main__":
    out = {rt: train_model(rt) for rt in FEATURES}
    print(json.dumps(out, indent=2))
