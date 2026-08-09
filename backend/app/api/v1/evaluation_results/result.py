from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.evaluation_results import (
    EvaluationResultCreate,
    EvaluationResultListResponse,
    EvaluationResultResponse,
    EvaluationResultStatisticsResponse,
    EvaluationResultUpdate,
)
from app.services.evaluation_results.result import EvaluationResultService


router = APIRouter(
    prefix="/evaluation-results",
    tags=["Evaluation Results"],
)


# @router.post(
#     "",
#     response_model=EvaluationResultResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_evaluation_result(
#     payload: EvaluationResultCreate,
#     db: AsyncSession = Depends(get_db),
# ):
#     result = await EvaluationResultService.create(
#         db,
#         evaluation_run_id=payload.evaluation_run_id,
#         dataset_case_id=payload.dataset_case_id,
#         status=payload.status,
#         actual_output=payload.actual_output,
#         expected_output=payload.expected_output,
#         scores=payload.scores,
#         feedback=payload.feedback,
#         trace=payload.trace,
#         latency_ms=payload.latency_ms,
#         input_tokens=payload.input_tokens,
#         output_tokens=payload.output_tokens,
#         total_tokens=payload.total_tokens,
#         error_message=payload.error_message,
#     )

#     return result


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


# @router.patch(
#     "/{result_id}",
#     response_model=EvaluationResultResponse,
# )
# async def update_evaluation_result(
#     result_id: UUID,
#     payload: EvaluationResultUpdate,
#     db: AsyncSession = Depends(get_db),
# ):
#     result = await EvaluationResultService.get_by_id(
#         db,
#         result_id,
#     )

#     if result is None or not result.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Evaluation result not found",
#         )

#     fields = payload.model_dump(exclude_unset=True)

#     result = await EvaluationResultService.update(
#         db,
#         result,
#         **fields,
#     )

#     return result


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

