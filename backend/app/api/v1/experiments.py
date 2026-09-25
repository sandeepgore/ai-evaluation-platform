from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.experiment.experiment import (
    ExperimentCreate,
    ExperimentResponse,
)
from app.services.experiment.experiment import ExperimentService
from app.schemas.experiment.snapshot import (
    ExperimentSnapshotCreate,
    ExperimentSnapshotResponse,
)

router = APIRouter(
    prefix="/experiments",
    tags=["Experiments"],
)


@router.post(
    "",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    service = ExperimentService(db)

    experiment = await service.create(data)

    return ExperimentResponse.model_validate(experiment)


@router.get(
    "",
    response_model=list[ExperimentResponse],
)
async def list_experiments(
    scope: str = Query(default="recent"),
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentResponse]:
    service = ExperimentService(db)

    try:
        experiments = await service.list(scope=scope)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return [ExperimentResponse.model_validate(experiment) for experiment in experiments]


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResponse,
)
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    service = ExperimentService(db)

    experiment = await service.get_by_id(experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    return ExperimentResponse.model_validate(experiment)


@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ExperimentService(db)

    experiment = await service.get_by_id(experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    await service.delete(experiment)


@router.post(
    "/{experiment_id}/snapshots",
    response_model=ExperimentSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_experiment_snapshot(
    experiment_id: UUID,
    data: ExperimentSnapshotCreate,
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)

    experiment = await service.get_by_id(experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    try:
        return await service.create_snapshot(
            experiment,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{experiment_id}/snapshots/{snapshot_id}",
    response_model=ExperimentSnapshotResponse,
    status_code=status.HTTP_200_OK,
)
async def get_experiment_snapshot(
    experiment_id: UUID,
    snapshot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ExperimentService(db)

    experiment = await service.get_by_id(experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    snapshot = await service.get_snapshot(
        experiment_id,
        snapshot_id,
    )

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment snapshot not found",
        )

    return snapshot
