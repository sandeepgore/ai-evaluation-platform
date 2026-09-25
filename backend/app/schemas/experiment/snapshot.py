from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExperimentSnapshotCreate(BaseModel):
    run_ids: list[UUID] = Field(min_length=1)


class ExperimentSnapshotResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    run_ids: list[UUID]
    run_results: dict[str, Any]
    comparison: dict[str, Any]
    calculation_version: int
