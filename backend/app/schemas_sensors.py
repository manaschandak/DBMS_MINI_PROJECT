"""Request and response shapes for sensors and readings."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SensorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sensor_type: Literal["TEMPERATURE", "COOLANT_FLOW", "ELECTRICAL"]
    location: str = Field(min_length=1, max_length=50)
    is_active: bool = True


class SensorOut(BaseModel):
    sensor_id: int
    battery_id: int
    sensor_type: str
    location: str
    is_active: bool


class TemperatureIn(BaseModel):
    sensor_id: int = Field(gt=0)
    recorded_at: datetime
    temperature_c: float = Field(ge=-50, le=200)
    data_source_id: int = Field(gt=0)


class ElectricalIn(BaseModel):
    sensor_id: int = Field(gt=0)
    recorded_at: datetime
    voltage_v: float = Field(ge=0, le=1000)
    current_a: float = Field(ge=-9999, le=9999)
    data_source_id: int = Field(gt=0)


class CoolantIn(BaseModel):
    sensor_id: int = Field(gt=0)
    recorded_at: datetime
    flow_rate_lpm: float = Field(ge=0, le=9999)
    inlet_temp_c: Optional[float] = Field(default=None, ge=-50, le=200)
    data_source_id: int = Field(gt=0)


class ReadingsBatch(BaseModel):
    temperature: list[TemperatureIn] = Field(default_factory=list, max_length=1000)
    electrical: list[ElectricalIn] = Field(default_factory=list, max_length=1000)
    coolant: list[CoolantIn] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def check_size(self):
        total = len(self.temperature) + len(self.electrical) + len(self.coolant)
        if total == 0:
            raise ValueError("Send at least one reading")
        if total > 1000:
            raise ValueError("At most 1000 readings per request")
        return self