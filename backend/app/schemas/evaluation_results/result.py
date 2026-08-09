from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# class EvaluationResultCreate(BaseModel):
#     evaluation_run_id: UUID
#     dataset_case_id: UUID

#     status: str = "pending"

#     actual_output: str | None = None
#     expected_output: str | None = None

#     scores: dict[str, Any] | None = None
#     feedback: str | None = None
#     trace: dict[str, Any] | None = None

#     latency_ms: int | None = None

#     input_tokens: int | None = None
#     output_tokens: int | None = None
#     total_tokens: int | None = None

#     error_message: str | None = None


# class EvaluationResultUpdate(BaseModel):
#     status: str | None = None

#     actual_output: str | None = None
#     expected_output: str | None = None

#     scores: dict[str, Any] | None = None
#     feedback: str | None = None
#     trace: dict[str, Any] | None = None

#     latency_ms: int | None = None

#     input_tokens: int | None = None
#     output_tokens: int | None = None
#     total_tokens: int | None = None

#     error_message: str | None = None


class EvaluationResultResponse(BaseModel):
    id: UUID

    evaluation_run_id: UUID
    dataset_case_id: UUID

    status: str

    actual_output: str | None = None
    expected_output: str | None = None

    scores: dict[str, Any] | None = None
    feedback: str | None = None
    trace: dict[str, Any] | None = None

    latency_ms: int | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    error_message: str | None = None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationResultListResponse(BaseModel):
    items: list[EvaluationResultResponse]
    total: int


class EvaluationResultStatisticsResponse(BaseModel):
    total: int
    completed: int
    failed: int
    pending: int

