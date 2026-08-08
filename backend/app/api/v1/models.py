from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.model import ModelCreate, ModelResponse, ModelUpdate
from app.services.model import ModelService


router = APIRouter(
    prefix="/models",
    tags=["Models"],
)


@router.post(
    "",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_model(
    data: ModelCreate,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    service = ModelService(db)
    return await service.create(data)


@router.get(
    "",
    response_model=list[ModelResponse],
)
async def list_models(
    project_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> list[ModelResponse]:
    service = ModelService(db)
    return await service.list(project_id)


@router.get(
    "/{model_id}",
    response_model=ModelResponse,
)
async def get_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    service = ModelService(db)
    return await service.get(model_id)


@router.patch(
    "/{model_id}",
    response_model=ModelResponse,
)
async def update_model(
    model_id: UUID,
    data: ModelUpdate,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    service = ModelService(db)
    return await service.update(model_id, data)


@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = ModelService(db)
    await service.delete(model_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)