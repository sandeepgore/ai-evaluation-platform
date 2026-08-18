from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetCaseCreate(BaseModel):
    dataset_version_id: UUID
    input: str = Field(min_length=1)
    expected_output: str | None = None
    case_metadata: dict[str, Any] | None = None


class DatasetCaseUpdate(BaseModel):
    input: str | None = Field(default=None, min_length=1)
    expected_output: str | None = None
    case_metadata: dict[str, Any] | None = None
    position: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class DatasetCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_version_id: UUID
    input: str
    expected_output: str | None
    case_metadata: dict[str, Any] | None
    position: int
    is_active: bool
