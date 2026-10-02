"""Request and response shapes for recommendations."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    battery_id: int = Field(gt=0)


class RecommendationOut(BaseModel):
    recommendation_id: int
    target_role: str
    battery_id: int
    serial_number: str
    source_type: str                      # RISK or ANOMALY
    assessment_id: Optional[int] = None
    anomaly_id: Optional[int] = None
    risk_level: Optional[str] = None
    anomaly_type: Optional[str] = None
    cause: Optional[str] = None
    recommendation_text: str
    created_at: datetime