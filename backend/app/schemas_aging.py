"""Request and response shapes for aging records."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AgingCreate(BaseModel):
    measured_at: datetime
    cycle_count: int = Field(ge=0, le=1000000)
    calendar_age_days: int = Field(ge=0, le=100000)
    capacity_ah: float = Field(gt=0, le=999999)
    internal_resistance_mohm: float = Field(gt=0, le=99999)
    data_source_id: int = Field(gt=0)


class AgingOut(BaseModel):
    aging_id: int
    battery_id: int
    measured_at: datetime
    cycle_count: int
    calendar_age_days: int
    capacity_ah: float
    internal_resistance_mohm: float
    data_source_id: int
    soh_pct: Optional[float] = None  # computed: capacity / nominal capacity * 100