from pydantic import BaseModel, ConfigDict


class EvaluatorResponse(BaseModel):
    name: str
    category: str
    description: str

    required_inputs: list[str]

    requires_reference: bool
    requires_context: bool
    requires_llm: bool

    applicable_to: list[str]
    tags: list[str]

    model_config = ConfigDict(from_attributes=True)


class EvaluatorListResponse(BaseModel):
    evaluators: list[EvaluatorResponse]
    total: int
