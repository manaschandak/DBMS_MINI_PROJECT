"""Request and response shapes (Pydantic validates these automatically)."""
from datetime import datetime

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