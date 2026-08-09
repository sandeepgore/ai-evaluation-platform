from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.evaluation_results import (
    EvaluationResultListResponse,
    EvaluationResultResponse,
    EvaluationResultStatisticsResponse,
)
from app.services.evaluation_results.result import EvaluationResultService


router = APIRouter(
    prefix="/evaluation-results",
    tags=["Evaluation Results"],
)



@router.get(
    "/{result_id}",
    response_model=EvaluationResultResponse,
)
async def get_evaluation_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await EvaluationResultService.get_by_id(
        db,
        result_id,
    )

    if result is None or not result.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation result not found",
        )

    return result


@router.get(
    "",
    response_model=EvaluationResultListResponse,
)
async def list_evaluation_results(
    evaluation_run_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await EvaluationResultService.list_by_run(
        db,
        evaluation_run_id,
    )




@router.delete(
    "/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_evaluation_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await EvaluationResultService.get_by_id(
        db,
        result_id,
    )

    if result is None or not result.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation result not found",
        )

    await EvaluationResultService.delete(
        db,
        result,
    )


@router.get(
    "/run/{evaluation_run_id}/statistics",
    response_model=EvaluationResultStatisticsResponse,
)
async def get_evaluation_run_statistics(
    evaluation_run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await EvaluationResultService.get_run_statistics(
        db,
        evaluation_run_id,
    )

