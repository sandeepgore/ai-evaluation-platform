from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.dataset_version import (
    DatasetVersionCreate,
    DatasetVersionResponse,
    DatasetVersionUpdate,
)
from app.services.dataset_version import DatasetVersionService

router = APIRouter(
    prefix="/dataset-versions",
    tags=["Dataset Versions"],
)


@router.post(
    "",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_version(
    data: DatasetVersionCreate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetVersionService(db)

    return await service.create(data)


@router.get(
    "",
    response_model=list[DatasetVersionResponse],
)
async def list_dataset_versions(
    dataset_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetVersionService(db)

    return await service.list(dataset_id)


@router.get(
    "/{version_id}",
    response_model=DatasetVersionResponse,
)
async def get_dataset_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetVersionService(db)

    return await service.get(version_id)


@router.patch(
    "/{version_id}",
    response_model=DatasetVersionResponse,
)
async def update_dataset_version(
    version_id: UUID,
    data: DatasetVersionUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetVersionService(db)

    return await service.update(version_id, data)


@router.delete(
    "/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetVersionService(db)

    await service.delete(version_id)

    return None