from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_type import EvaluationType
from app.shared.enums import DataPolicy


class DataPolicyConfiguration(BaseModel):
    type: DataPolicy = DataPolicy.STRICT
    threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_threshold(self) -> "DataPolicyConfiguration":
        if self.type == DataPolicy.THRESHOLD and self.threshold is None:
            raise ValueError("threshold is required when data policy type is 'threshold'.")

        if self.type != DataPolicy.THRESHOLD and self.threshold is not None:
            raise ValueError(
                "threshold can only be configured when data policy type is 'threshold'."
            )

        return self


class EvaluationRunCreate(BaseModel):
    dataset_version_id: UUID
    model_id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    evaluation_type: EvaluationType = EvaluationType.TEXT
    configuration: dict[str, Any] | None = None


class EvaluationRunUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    status: EvaluationRunStatus | None = None
    evaluation_type: EvaluationType | None = None
    configuration: dict[str, Any] | None = None
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
    evaluation_type: EvaluationType
    configuration: dict[str, Any] | None
    total_cases: int
    completed_cases: int
    failed_cases: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None

    model_config = ConfigDict(from_attributes=True)
