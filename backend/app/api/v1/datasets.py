from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.dataset.dataset import Dataset
from app.schemas.dataset.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)
from app.schemas.dataset_ingestion.dataset_import import DatasetImportPayload
from app.schemas.dataset_version.dataset_version import DatasetVersionResponse
from app.services.dataset.dataset import DatasetService
from app.services.dataset_ingestion.parser import (
    MAX_DATASET_FILE_BYTES,
    parse_tabular_dataset,
)
from app.services.dataset_ingestion.service import DatasetImportService

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


@router.post(
    "/{dataset_id}/import",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_dataset(
    dataset_id: UUID,
    data: DatasetImportPayload,
    request: Request,
    filename: str | None = Query(default=None, max_length=255),
    db: AsyncSession = Depends(get_db),
):
    dataset = await db.get(Dataset, dataset_id)
    request.state.audit_context = {
        "dataset_name": dataset.name if dataset else None,
        "source_file": {
            "name": filename,
            "format": "json" if filename else "json payload",
            "case_count": len(data.cases),
        },
    }
    service = DatasetImportService(db)

    return await service.import_json(
        dataset_id=dataset_id,
        payload=data,
    )


@router.post(
    "/{dataset_id}/import-file",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_dataset_file(
    dataset_id: UUID,
    request: Request,
    filename: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    dataset = await db.get(Dataset, dataset_id)
    request.state.audit_context = {
        "dataset_name": dataset.name if dataset else None,
        "source_file": {
            "name": filename,
            "format": filename.rsplit(".", 1)[-1].lower(),
        },
    }
    content_parts: list[bytes] = []
    total_size = 0
    async for chunk in request.stream():
        total_size += len(chunk)
        request.state.audit_context["source_file"]["size_bytes"] = total_size
        if total_size > MAX_DATASET_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Dataset files must be 10 MB or smaller.",
            )
        content_parts.append(chunk)

    content = b"".join(content_parts)
    payload = parse_tabular_dataset(filename, content)
    request.state.audit_context["source_file"]["case_count"] = len(payload.cases)
    service = DatasetImportService(db)
    return await service.import_json(dataset_id=dataset_id, payload=payload)


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

    try:
        deleted = await service.delete(dataset_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
