"""Request and response shapes for anomalies."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DetectRequest(BaseModel):
    battery_id: int = Field(gt=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AnomalyOut(BaseModel):
    anomaly_id: int
    sensor_id: int
    battery_id: int
    location: str
    detected_at: datetime
    anomaly_type: str
    cause: str
    detection_method: str
    anomaly_score: Optional[float] = None
    details: Optional[str] = None