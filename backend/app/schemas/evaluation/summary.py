from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationRunModelResponse(BaseModel):
    id: UUID
    name: str
    provider: str
    model_identifier: str


class EvaluationRunFeedbackResponse(BaseModel):
    """
    Feedback structure used by the rolling reducer.

    Intermediate reducer states are allowed to contain
    fewer than three items in each section.
    """

    overall: str

    strengths: list[str]
    weaknesses: list[str]
    patterns: list[str]
    recommendations: list[str]
    evaluator_feedback: list[str] = Field(
        default_factory=list,
    )


class EvaluationRunFinalFeedbackResponse(BaseModel):
    """
    Final qualitative feedback persisted with the evaluation summary.

    The final summary must contain at least three evidence-grounded
    items in each qualitative section.
    """

    overall: str = Field(
        min_length=1,
    )

    strengths: list[str] = Field(
        min_length=3,
    )

    weaknesses: list[str] = Field(
        min_length=3,
    )

    patterns: list[str] = Field(
        min_length=3,
    )

    recommendations: list[str] = Field(
        min_length=3,
    )

    evaluator_feedback: list[str] = Field(
        default_factory=list,
    )


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

    overall_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    metrics: dict[str, float]

    feedback: EvaluationRunFinalFeedbackResponse

    total_results: int = Field(ge=0)
    completed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)

    performance: EvaluationRunPerformanceResponse
