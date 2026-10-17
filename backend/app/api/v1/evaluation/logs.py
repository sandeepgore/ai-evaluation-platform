from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.evaluation.evaluation import EvaluationRunService
from app.services.evaluation.log_download import (
    LOGS_NOT_AVAILABLE,
    archive_evaluation_run_logs,
    archive_scheduler_logs,
    evaluation_run_logs_available,
    scheduler_logs_available,
)

run_logs_router = APIRouter(prefix="/evaluation-runs", tags=["Evaluation Logs"])
scheduler_logs_router = APIRouter(prefix="/evaluation-scheduler", tags=["Evaluation Logs"])


@run_logs_router.get("/{run_id}/logs/availability")
async def get_evaluation_run_logs_availability(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    run = await EvaluationRunService.get_by_id(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )
    return {"available": evaluation_run_logs_available(run_id)}


@run_logs_router.get("/{run_id}/logs")
async def download_evaluation_run_logs(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    run = await EvaluationRunService.get_by_id(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )

    try:
        archive = archive_evaluation_run_logs(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or LOGS_NOT_AVAILABLE,
        ) from exc

    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="evaluation-run-{run_id}-logs.zip"',
        },
    )


@scheduler_logs_router.get("/logs/availability")
async def get_scheduler_logs_availability() -> dict[str, bool]:
    return {"available": scheduler_logs_available()}


@scheduler_logs_router.get("/logs")
async def download_scheduler_logs() -> StreamingResponse:
    try:
        archive: BytesIO = archive_scheduler_logs()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or LOGS_NOT_AVAILABLE,
        ) from exc

    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="evaluation-scheduler-logs.zip"',
        },
    )
