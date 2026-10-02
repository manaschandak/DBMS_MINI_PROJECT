"""Response shapes for alerts."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertOut(BaseModel):
    alert_id: int
    battery_id: int
    serial_number: str
    priority_code: str
    severity_level: int
    final_risk_level: str
    message: str
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None