"""Response model for alerts."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

PriorityCode = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class AlertOut(BaseModel):
    alert_id: int
    priority_code: str
    severity_level: int
    battery_id: int
    serial_number: str
    risk_type: Optional[str] = None
    final_risk_level: str
    message: Optional[str] = None
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None