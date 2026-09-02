from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetImportCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: str = Field(min_length=1)
    expected_output: str | None = None
    metadata: dict[str, Any] | None = None


class DatasetImportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cases: list[DatasetImportCase] = Field(min_length=1)
