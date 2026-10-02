"""Risk prediction contract.

    predict_risk(features, risk_type) -> {"level": str, "confidence": float or None}

THIS IS A PLACEHOLDER: simple fixed rules, NOT a trained model.
When a real model exists, replace the body of predict_risk() and keep the same
inputs and output. Nothing else in the backend has to change.
"""

MODEL_KIND = "PLACEHOLDER_RULES"


def predict_risk(features: dict, risk_type: str) -> dict:
    if risk_type == "THERMAL":
        temp = features["max_temp_c"]
        if temp < 35:
            level = "LOW"
        elif temp < 45:
            level = "MEDIUM"
        else:
            level = "HIGH"  # CRITICAL comes only from the hard safety rule in the router
    elif risk_type == "HEALTH":
        capacity = features["capacity_pct"]
        if capacity >= 95:
            level = "LOW"
        elif capacity >= 90:
            level = "MEDIUM"
        elif capacity >= 80:
            level = "HIGH"
        else:
            level = "CRITICAL"
    else:
        raise ValueError("Unknown risk_type: " + str(risk_type))

    # No confidence: fixed rules are not probabilistic, and inventing a number would mislead.
    return {"level": level, "confidence": None}