from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperimentSnapshotCreate(BaseModel):
    run_ids: list[UUID] = Field(min_length=1)


class ExperimentSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    run_ids: list[UUID]
    run_results: dict[str, Any]
    comparison: dict[str, Any]
    calculation_version: int
    created_at: datetime
