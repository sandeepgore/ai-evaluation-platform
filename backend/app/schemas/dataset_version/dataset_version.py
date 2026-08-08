from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.dataset_version.version import DatasetVersionStatus


class DatasetVersionCreate(BaseModel):
    dataset_id: UUID
    version: int = Field(ge=1)
    status: DatasetVersionStatus = DatasetVersionStatus.DRAFT
    description: str | None = None


class DatasetVersionUpdate(BaseModel):
    status: DatasetVersionStatus | None = None
    description: str | None = None
    is_active: bool | None = None


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    version: int
    status: DatasetVersionStatus
    description: str | None
    case_count: int
    is_active: bool