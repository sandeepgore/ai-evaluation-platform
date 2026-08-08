from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.model import ModelProvider, ModelType


class ModelCreate(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=150)
    provider: ModelProvider
    model_identifier: str = Field(min_length=1, max_length=150)
    model_type: ModelType = ModelType.CHAT
    configuration: dict[str, Any] | None = None


class ModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    provider: ModelProvider | None = None
    model_identifier: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    model_type: ModelType | None = None
    configuration: dict[str, Any] | None = None
    is_active: bool | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    provider: ModelProvider
    model_identifier: str
    model_type: ModelType
    configuration: dict[str, Any] | None
    is_active: bool