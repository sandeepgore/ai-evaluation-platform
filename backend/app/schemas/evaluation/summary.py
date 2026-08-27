from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationRunModelResponse(BaseModel):
    id: UUID
    name: str
    provider: str
    model_identifier: str


class EvaluationRunFeedbackResponse(BaseModel):
    overall: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    evaluator_feedback: list[str]


class EvaluationRunCostResponse(BaseModel):
    input_cost: float = Field(ge=0)
    output_cost: float = Field(ge=0)
    total_cost: float = Field(ge=0)
    currency: str = "USD"


class EvaluationRunPerformanceResponse(BaseModel):
    duration_ms: int | None = Field(None, ge=0)

    total_model_latency_ms: int = Field(ge=0)
    avg_model_latency_ms: float | None = Field(None, ge=0)

    min_model_latency_ms: int | None = Field(None, ge=0)
    p50_model_latency_ms: float | None = Field(None, ge=0)
    p95_model_latency_ms: float | None = Field(None, ge=0)
    p99_model_latency_ms: float | None = Field(None, ge=0)
    max_model_latency_ms: int | None = Field(None, ge=0)

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    throughput_cases_per_second: float | None = Field(None, ge=0)

    cost: EvaluationRunCostResponse


class EvaluationRunSummaryResponse(BaseModel):
    model: EvaluationRunModelResponse | None = None

    overall_score: float = Field(ge=0.0, le=1.0)
    metrics: dict[str, float]

    feedback: EvaluationRunFeedbackResponse

    total_results: int = Field(ge=0)
    completed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)

    performance: EvaluationRunPerformanceResponse
