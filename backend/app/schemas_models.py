"""Request and response shapes for the models and model-performance endpoints."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ModelOut(BaseModel):
    model_id: int
    model_name: str
    version: str
    task_type: str
    algorithm: str
    risk_type: Optional[str] = None
    trained_at: Optional[datetime] = None
    is_active: bool
    notes: Optional[str] = None


class PerformanceOut(BaseModel):
    performance_id: int
    model_id: int
    model_name: str
    version: str
    evaluation_type: str
    sample_count: int
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    recall_high_critical: Optional[float] = None
    evaluated_at: datetime
    notes: Optional[str] = None


class LiveAccuracyOut(BaseModel):
    model_id: int
    model_name: str
    risk_type: Optional[str] = None
    feedback_count: int
    exact_matches: int
    accuracy: Optional[float] = None
    underestimated: int


class EvaluateRequest(BaseModel):
    model_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Evaluate one model. Leave empty to evaluate every model that has feedback.",
    )


class EvaluateResult(BaseModel):
    saved: List[PerformanceOut]
    skipped_model_ids: List[int]  # models with no feedback yet, so nothing to measure
