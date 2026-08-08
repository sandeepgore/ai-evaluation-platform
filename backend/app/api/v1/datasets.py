from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.dataset.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)
from app.services.dataset.dataset import DatasetService

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset(
    data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)

    try:
        dataset = await service.create(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return dataset


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)

    dataset = await service.get(dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset


@router.get(
    "",
    response_model=list[DatasetResponse],
)
async def list_datasets(
    project_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)

    return await service.list_by_project(project_id)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
async def update_dataset(
    dataset_id: UUID,
    data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)

    try:
        dataset = await service.update(dataset_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = DatasetService(db)

    deleted = await service.delete(dataset_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )