from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.dataset_version.version import DatasetVersionStatus


class DatasetVersionCreate(BaseModel):
    dataset_id: UUID
    description: str | None = None


class DatasetVersionUpdate(BaseModel):
    description: str | None = None
    is_active: bool | None = None


class DatasetVersionAnalytics(BaseModel):
    case_count: int
    reference_count: int
    context_count: int
    reference_coverage: float
    context_coverage: float


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    version: int
    status: DatasetVersionStatus
    description: str | None
    case_count: int
    analytics: DatasetVersionAnalytics | None
    is_active: bool
