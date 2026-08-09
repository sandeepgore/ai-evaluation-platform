from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.evaluation import (
    EvaluationRunCreate,
    EvaluationRunResponse,
    EvaluationRunUpdate,
)
from app.services.evaluation import EvaluationRunService


router = APIRouter(
    prefix="/evaluation-runs",
    tags=["Evaluation Runs"],
)


@router.post(
    "",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_run(
    data: EvaluationRunCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await EvaluationRunService.create(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[EvaluationRunResponse],
)
async def list_evaluation_runs(
    dataset_version_id: UUID | None = Query(default=None),
    model_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await EvaluationRunService.list(
        db,
        dataset_version_id=dataset_version_id,
        model_id=model_id,
    )


@router.get(
    "/{run_id}",
    response_model=EvaluationRunResponse,
)
async def get_evaluation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await EvaluationRunService.get_by_id(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )

    return run


@router.patch(
    "/{run_id}",
    response_model=EvaluationRunResponse,
)
async def update_evaluation_run(
    run_id: UUID,
    data: EvaluationRunUpdate,
    db: AsyncSession = Depends(get_db),
):
    run = await EvaluationRunService.get_by_id(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )

    return await EvaluationRunService.update(db, run, data)


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_evaluation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await EvaluationRunService.get_by_id(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )

    await EvaluationRunService.delete(db, run)