"""Synthetic training data for the risk models.

!! SYNTHETIC !! Labels come from documented threshold rules plus measurement
noise. They are NOT real battery failure labels. Anything trained on this
must be reported as "synthetic" (see DATASET_NAME).
"""
import numpy as np
import pandas as pd

DATASET_NAME = "synthetic_threshold_rules_v1"
LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Features each model uses. Add columns here (and in _sample) to extend.
FEATURES = {
    "THERMAL": ["max_temp_c"],
    "HEALTH": ["capacity_pct"],
}

# (upper bound, level) checked in order; used to assign the TRUE label.
THERMAL_RULES = [(40, "LOW"), (50, "MEDIUM"), (60, "HIGH")]  # >=60 CRITICAL
# Health: lower capacity = worse. 80% is the usual end-of-life mark.
HEALTH_RULES = [(70, "CRITICAL"), (80, "HIGH"), (90, "MEDIUM")]  # >=90 LOW


def _label_thermal(t):
    for bound, lvl in THERMAL_RULES:
        if t < bound:
            return lvl
    return "CRITICAL"


def _label_health(c):
    for bound, lvl in HEALTH_RULES:
        if c < bound:
            return lvl
    return "LOW"


def generate_data(risk_type: str, n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame with the model's feature columns plus 'label'."""
    if risk_type not in FEATURES:
        raise ValueError(f"risk_type must be one of {list(FEATURES)}")
    rng = np.random.default_rng(seed)
    if risk_type == "THERMAL":
        true_val = rng.uniform(20, 80, n)
        observed = true_val + rng.normal(0, 2.0, n)   # sensor noise
        labels = [_label_thermal(v) for v in true_val]
        df = pd.DataFrame({"max_temp_c": observed.round(2)})
    else:
        true_val = rng.uniform(55, 100, n)
        observed = np.clip(true_val + rng.normal(0, 1.5, n), 0, 100)
        labels = [_label_health(v) for v in true_val]
        df = pd.DataFrame({"capacity_pct": observed.round(2)})
    df["label"] = labels
    return df


if __name__ == "__main__":
    for rt in FEATURES:
        d = generate_data(rt)
        print(rt, DATASET_NAME, len(d))
        print(d["label"].value_counts().to_string(), "\n")
