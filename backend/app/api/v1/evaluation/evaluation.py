from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.db.session import get_db
from app.schemas.evaluation import (
    EvaluationRunCreate,
    EvaluationRunResponse,
    EvaluationRunUpdate,
)
from app.schemas.evaluation.summary import EvaluationRunSummaryResponse
from app.services.evaluation import EvaluationRunService
from app.services.evaluation.run_validation import EvaluationRunValidationError
from app.services.evaluation_engine.cache import EvaluationSummaryCache
from app.services.evaluation_engine.engine import EvaluationEngine
from app.services.evaluation_engine.scoring_config import (
    ScoringConfigurationService,
)
from app.services.evaluation_engine.summary import EvaluationRunSummaryService
from app.services.evaluation_engine.summary_persistence import (
    EvaluationSummaryPersistenceService,
)
from app.services.evaluators import create_default_registry
from app.services.evaluators.applicability import (
    EvaluatorApplicabilityService,
)
from app.services.scoring import ScoringService

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
    except EvaluationRunValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


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


@router.get(
    "/{run_id}/summary",
    response_model=EvaluationRunSummaryResponse,
)
async def get_evaluation_run_summary(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    cache = EvaluationSummaryCache(redis)

    # --------------------------------------------------------------
    # 1. Redis cache
    # --------------------------------------------------------------

    try:
        cached_summary = await cache.get(run_id)

        if cached_summary is not None:
            return cached_summary

    except Exception:
        # Cache is optional. PostgreSQL remains authoritative.
        pass

    # --------------------------------------------------------------
    # 2. Persisted PostgreSQL summary
    # --------------------------------------------------------------

    persisted_summary = await EvaluationSummaryPersistenceService.get(
        db,
        run_id,
    )

    if persisted_summary is not None:
        performance = (
            persisted_summary.performance if isinstance(persisted_summary.performance, dict) else {}
        )

        summary = {
            "model": (
                persisted_summary.metadata.get("model")
                if isinstance(persisted_summary.metadata, dict)
                else None
            ),
            "overall_score": persisted_summary.overall_score,
            "metrics": persisted_summary.metrics,
            "feedback": persisted_summary.feedback,
            "total_results": performance.get(
                "total_results",
                0,
            ),
            "completed_cases": performance.get(
                "completed_cases",
                0,
            ),
            "failed_cases": performance.get(
                "failed_cases",
                0,
            ),
            "not_applicable_cases": performance.get(
                "not_applicable_cases",
                0,
            ),
            "performance": performance,
        }

        try:
            await cache.set(
                run_id,
                summary,
            )
        except Exception:
            pass

        return summary

    # --------------------------------------------------------------
    # 3. Fallback calculation
    # --------------------------------------------------------------

    summary = await EvaluationRunSummaryService.calculate(
        db,
        run_id,
    )

    # --------------------------------------------------------------
    # 4. Cache calculated fallback
    # --------------------------------------------------------------

    try:
        await cache.set(
            run_id,
            summary,
        )
    except Exception:
        pass

    return summary


@router.post(
    "/{run_id}/execute",
    response_model=EvaluationRunResponse,
)
async def execute_evaluation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    evaluator_registry = create_default_registry()

    applicability_service = EvaluatorApplicabilityService(
        evaluator_registry,
    )

    scoring_service = ScoringService()

    scoring_configuration_service = ScoringConfigurationService(
        redis=redis,
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=None,
        evaluator_registry=evaluator_registry,
        applicability_service=applicability_service,
        scoring_service=scoring_service,
        scoring_configuration_service=scoring_configuration_service,
        redis=redis,
    )

    return await engine.execute(run_id)
