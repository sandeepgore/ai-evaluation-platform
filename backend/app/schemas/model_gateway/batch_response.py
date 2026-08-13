from typing import Any

from pydantic import BaseModel, Field

from app.schemas.model_gateway.response import ModelResponse


class BatchModelResponse(BaseModel):
    """
    Result for one item in a batch model inference request.

    Exactly one of response or error should normally be populated.
    """

    response: ModelResponse | None = None

    error: dict[str, Any] | None = None

    index: int = Field(ge=0)
