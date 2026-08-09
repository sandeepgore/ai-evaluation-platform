from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluation import EvaluationRunStatus


class EvaluationRunCreate(BaseModel):
    dataset_version_id: UUID
    model_id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    configuration: dict[str, Any] | None = None


class EvaluationRunUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    status: EvaluationRunStatus | None = None
    configuration: dict[str, Any] | None = None
    summary_feedback: str | None = None
    total_cases: int | None = Field(None, ge=0)
    completed_cases: int | None = Field(None, ge=0)
    failed_cases: int | None = Field(None, ge=0)
    is_active: bool | None = None


class EvaluationRunResponse(BaseModel):
    id: UUID
    dataset_version_id: UUID
    model_id: UUID
    name: str
    status: EvaluationRunStatus
    configuration: dict[str, Any] | None
    summary_feedback: str | None
    total_cases: int
    completed_cases: int
    failed_cases: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)