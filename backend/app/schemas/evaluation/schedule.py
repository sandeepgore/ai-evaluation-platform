from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.evaluation import EvaluationScheduleType
from app.models.evaluation.evaluation_type import EvaluationType


class EvaluationScheduleCreate(BaseModel):
    dataset_version_id: UUID
    model_id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    evaluation_type: EvaluationType = EvaluationType.TEXT
    configuration: dict[str, Any] | None = None
    schedule_type: EvaluationScheduleType
    schedule_expression: str | None = Field(
        default=None,
        max_length=100,
    )
    timezone: str = Field(
        default="UTC",
        min_length=1,
        max_length=100,
    )
    next_run_at: datetime | None = None

    @model_validator(mode="after")
    def validate_schedule(self) -> "EvaluationScheduleCreate":
        if self.schedule_type == EvaluationScheduleType.ONE_TIME:
            if self.next_run_at is None:
                raise ValueError("next_run_at is required for one-time schedules.")

            if self.schedule_expression is not None:
                raise ValueError("schedule_expression must be omitted for one-time schedules.")

        if self.schedule_type == EvaluationScheduleType.RECURRING:
            if self.schedule_expression is None:
                raise ValueError("schedule_expression is required for recurring schedules.")

            if self.next_run_at is not None:
                raise ValueError("next_run_at must be omitted for recurring schedules.")

        return self


class EvaluationScheduleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    configuration: dict[str, Any] | None = None
    schedule_expression: str | None = Field(
        default=None,
        max_length=100,
    )
    timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    is_active: bool | None = None


class EvaluationScheduleResponse(BaseModel):
    id: UUID
    dataset_version_id: UUID
    model_id: UUID
    name: str
    evaluation_type: EvaluationType
    configuration: dict[str, Any] | None
    schedule_type: EvaluationScheduleType
    schedule_expression: str | None
    timezone: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
