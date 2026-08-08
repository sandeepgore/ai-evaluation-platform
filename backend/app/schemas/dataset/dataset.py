from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.dataset.dataset import DatasetType


class DatasetCreate(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=100)
    description: str | None = None
    dataset_type: DatasetType = DatasetType.CUSTOM


class DatasetUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = None
    dataset_type: DatasetType | None = None
    is_active: bool | None = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    slug: str
    description: str | None
    dataset_type: DatasetType
    is_active: bool