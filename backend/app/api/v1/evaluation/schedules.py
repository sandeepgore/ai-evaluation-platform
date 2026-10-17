from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.evaluation import (
    EvaluationScheduleCreate,
    EvaluationScheduleResponse,
    EvaluationScheduleUpdate,
)
from app.services.evaluation.schedule import EvaluationScheduleService

router = APIRouter(
    prefix="/evaluation-schedules",
    tags=["Evaluation Schedules"],
)


@router.post(
    "",
    response_model=EvaluationScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_schedule(
    data: EvaluationScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> EvaluationScheduleResponse:
    try:
        schedule = await EvaluationScheduleService.create(db, data)
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message in {
            "Dataset version not found",
            "Model not found",
        } else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message) from exc

    return EvaluationScheduleResponse.model_validate(schedule)


@router.get(
    "",
    response_model=list[EvaluationScheduleResponse],
)
async def list_evaluation_schedules(
    dataset_version_id: UUID | None = Query(default=None),
    model_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EvaluationScheduleResponse]:
    schedules = await EvaluationScheduleService.list(
        db,
        dataset_version_id=dataset_version_id,
        model_id=model_id,
    )
    return [EvaluationScheduleResponse.model_validate(item) for item in schedules]


@router.get(
    "/{schedule_id}",
    response_model=EvaluationScheduleResponse,
)
async def get_evaluation_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EvaluationScheduleResponse:
    schedule = await EvaluationScheduleService.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation schedule not found",
        )
    return EvaluationScheduleResponse.model_validate(schedule)


@router.patch(
    "/{schedule_id}",
    response_model=EvaluationScheduleResponse,
)
async def update_evaluation_schedule(
    schedule_id: UUID,
    data: EvaluationScheduleUpdate,
    db: AsyncSession = Depends(get_db),
) -> EvaluationScheduleResponse:
    schedule = await EvaluationScheduleService.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation schedule not found",
        )
    try:
        schedule = await EvaluationScheduleService.update(db, schedule, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return EvaluationScheduleResponse.model_validate(schedule)


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_evaluation_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    schedule = await EvaluationScheduleService.get_by_id(db, schedule_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation schedule not found",
        )
    await EvaluationScheduleService.delete(db, schedule)
