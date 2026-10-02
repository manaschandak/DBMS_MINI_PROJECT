"""Request and response models for feedback."""
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from pydantic import AwareDatetime, BaseModel, Field, field_validator

Outcome = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
OutcomeSource = Literal["SERVICE_INSPECTION", "LAB_TEST", "FIELD_OBSERVATION", "SIMULATION"]
Role = Literal["ADMIN", "BMS_ENGINEER", "FLEET_OPERATOR", "SERVICE_TECHNICIAN", "RESEARCHER"]


class FeedbackCreate(BaseModel):
    prediction_id: int = Field(ge=1)
    actual_outcome: Outcome
    outcome_source: OutcomeSource
    submitted_by_role: Role
    observed_at: Optional[AwareDatetime] = None  # must include a timezone, e.g. +05:30
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("observed_at")
    @classmethod
    def not_in_future(cls, value):
        if value is not None and value > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("observed_at cannot be in the future")
        return value

    @field_validator("notes")
    @classmethod
    def blank_notes_become_none(cls, value):
        if value is not None and not value.strip():
            return None
        return value


class FeedbackOut(BaseModel):
    feedback_id: int
    prediction_id: int
    serial_number: str
    risk_type: Optional[str] = None
    predicted_label: str
    actual_outcome: str
    matches_prediction: bool
    outcome_source: str
    submitted_by_role: str
    observed_at: datetime
    notes: Optional[str] = None
    created_at: datetime