"""Request and response shapes for digital twins and CFD simulations."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TwinCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    battery_id: int = Field(gt=0)
    model_version: str = Field(min_length=1, max_length=30)
    last_synced_at: Optional[datetime] = None
    simulated_soh_pct: Optional[float] = Field(default=None, ge=0, le=100)


class TwinOut(BaseModel):
    twin_id: int
    battery_id: int
    model_version: str
    last_synced_at: Optional[datetime] = None
    simulated_soh_pct: Optional[float] = None


class CfdCreate(BaseModel):
    twin_id: int = Field(gt=0)
    run_at: Optional[datetime] = None
    flow_rate_lpm: float = Field(gt=0, le=9999)
    inlet_temp_c: float = Field(ge=-50, le=200)
    max_temp_c: float = Field(ge=-50, le=200)
    avg_temp_c: float = Field(ge=-50, le=200)
    pressure_drop_kpa: Optional[float] = Field(default=None, ge=0, le=99999)
    data_source_id: int = Field(gt=0)

    @model_validator(mode="after")
    def max_not_below_avg(self):
        if self.max_temp_c < self.avg_temp_c:
            raise ValueError("max_temp_c must be greater than or equal to avg_temp_c")
        return self


class CfdOut(BaseModel):
    simulation_id: int
    twin_id: int
    run_at: datetime
    flow_rate_lpm: float
    inlet_temp_c: float
    max_temp_c: float
    avg_temp_c: float
    pressure_drop_kpa: Optional[float] = None
    data_source_id: int


class TwinDetail(TwinOut):
    simulations: list[CfdOut] = []