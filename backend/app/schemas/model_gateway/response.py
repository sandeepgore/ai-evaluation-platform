from typing import Any

from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    """
    Standard response returned by a model provider.

    The evaluation engine consumes this response without
    depending on a specific model provider.
    """

    output: str

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)

    latency_ms: float = Field(default=0.0, ge=0)

    trace: dict[str, Any] = Field(default_factory=dict)