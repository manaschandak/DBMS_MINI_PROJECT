"""Request and response models for predictions."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

RiskType = Literal["THERMAL", "HEALTH"]


class PredictionRequest(BaseModel):
    battery_id: int = Field(ge=1)
    risk_type: RiskType
    notes: Optional[str] = Field(default=None, max_length=200)

    @field_validator("notes")
    @classmethod
    def blank_notes_become_none(cls, value):
        if value is not None and not value.strip():
            return None
        return value


class PredictionCreated(BaseModel):
    prediction_id: int
    assessment_id: int
    battery_id: int
    serial_number: str
    risk_type: str
    model_name: str
    model_kind: str
    predicted_label: str
    confidence: Optional[float] = None
    final_risk_level: str
    rule_override: bool
    alert_id: Optional[int] = None
    recommendations_created: int
    predicted_at: datetime
    notes: Optional[str] = None


class PredictionOut(BaseModel):
    prediction_id: int
    battery_id: int
    serial_number: str
    risk_type: Optional[str] = None
    model_name: str
    predicted_label: str
    confidence: Optional[float] = None
    final_risk_level: Optional[str] = None
    rule_override: Optional[bool] = None
    predicted_at: datetime
    notes: Optional[str] = None