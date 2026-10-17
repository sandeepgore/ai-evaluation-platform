from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperimentCreate(BaseModel):
    project_id: UUID | None = None
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
