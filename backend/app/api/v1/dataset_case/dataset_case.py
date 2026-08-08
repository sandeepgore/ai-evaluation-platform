from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.dataset_case import (
    DatasetCaseCreate,
    DatasetCaseResponse,
    DatasetCaseUpdate,
)
from app.services.dataset_case import DatasetCaseService


router = APIRouter(
    prefix="/dataset-cases",
    tags=["Dataset Cases"],
)


@router.post(
    "",
    response_model=DatasetCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_case(
    data: DatasetCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    return await DatasetCaseService.create(db, data)


@router.get(
    "",
    response_model=list[DatasetCaseResponse],
)
async def list_dataset_cases(
    dataset_version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await DatasetCaseService.list(
        db,
        dataset_version_id,
    )


@router.get(
    "/{case_id}",
    response_model=DatasetCaseResponse,
)
async def get_dataset_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await DatasetCaseService.get(
        db,
        case_id,
    )


@router.patch(
    "/{case_id}",
    response_model=DatasetCaseResponse,
)
async def update_dataset_case(
    case_id: UUID,
    data: DatasetCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await DatasetCaseService.update(
        db,
        case_id,
        data,
    )


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await DatasetCaseService.delete(
        db,
        case_id,
    )