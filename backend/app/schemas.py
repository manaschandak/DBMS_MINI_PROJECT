"""Request and response shapes (Pydantic validates these automatically)."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ManufacturerCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    manufacturer_name: str = Field(min_length=1, max_length=100)


class ManufacturerOut(BaseModel):
    manufacturer_id: int
    manufacturer_name: str
    created_at: datetime


class ChemistryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    chemistry_code: str = Field(min_length=1, max_length=10)
    chemistry_name: str = Field(min_length=1, max_length=100)


class ChemistryOut(BaseModel):
    chemistry_id: int
    chemistry_code: str
    chemistry_name: str


class BatteryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    serial_number: str = Field(min_length=1, max_length=50)
    battery_type: Literal["PACK", "CELL"] = "PACK"
    manufacturer_id: int = Field(gt=0)
    chemistry_id: int = Field(gt=0)
    nominal_capacity_ah: float = Field(gt=0, le=100000)
    install_date: Optional[date] = None
    status: Literal["ACTIVE", "MAINTENANCE", "RETIRED"] = "ACTIVE"


class BatteryOut(BaseModel):
    battery_id: int
    serial_number: str
    battery_type: str
    manufacturer_id: int
    manufacturer_name: str
    chemistry_id: int
    chemistry_code: str
    nominal_capacity_ah: float
    install_date: Optional[date] = None
    status: str