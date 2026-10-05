from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_version import DatasetVersion
from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.model import Model
from app.schemas.evaluation import EvaluationRunCreate, EvaluationRunUpdate
from app.services.evaluation.run_validation import (
    EvaluationRunValidationService,
)
from app.services.evaluators import create_default_registry


class EvaluationRunService:
    @staticmethod
    def validate_status_transition(
        current_status: EvaluationRunStatus,
        new_status: EvaluationRunStatus,
    ) -> bool:
        """
        Validate whether an evaluation run can transition
        from the current status to the new status.

            Terminal states:
                COMPLETED
                FAILED
                CANCELLED

            Valid transitions:
                PENDING   -> RUNNING
                PENDING   -> CANCELLED
                RUNNING   -> COMPLETED
                RUNNING   -> FAILED
                RUNNING   -> CANCELLED

            Re-applying the same status is allowed.
        """

        if current_status == new_status:
            return True

        allowed_transitions = {
            EvaluationRunStatus.PENDING: {
                EvaluationRunStatus.RUNNING,
                EvaluationRunStatus.CANCELLED,
            },
            EvaluationRunStatus.RUNNING: {
                EvaluationRunStatus.COMPLETED,
                EvaluationRunStatus.FAILED,
                EvaluationRunStatus.CANCELLED,
            },
            EvaluationRunStatus.COMPLETED: set(),
            EvaluationRunStatus.FAILED: set(),
            EvaluationRunStatus.CANCELLED: set(),
        }

        allowed_statuses = allowed_transitions.get(
            current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise ValueError(
                f"Invalid evaluation run status transition: "
                f"{current_status.value} -> {new_status.value}"
            )

        return True

    @staticmethod
    async def create(
        db: AsyncSession,
        data: EvaluationRunCreate,
        *,
        commit: bool = True,
    ) -> EvaluationRun:
        # --------------------------------------------------------------
        # Verify dataset version exists
        # --------------------------------------------------------------

        dataset_version_result = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == data.dataset_version_id,
                DatasetVersion.is_active.is_(True),
            )
        )

        dataset_version = dataset_version_result.scalar_one_or_none()

        if dataset_version is None:
            raise ValueError("Dataset version not found")

        # --------------------------------------------------------------
        # Verify model exists
        # --------------------------------------------------------------

        model_result = await db.execute(
            select(Model).where(
                Model.id == data.model_id,
                Model.is_active.is_(True),
            )
        )

        model = model_result.scalar_one_or_none()

        if model is None:
            raise ValueError("Model not found")

        # --------------------------------------------------------------
        # Validate evaluation run before creation
        # --------------------------------------------------------------

        evaluator_registry = create_default_registry()

        validation_service = EvaluationRunValidationService(
            evaluator_registry,
        )

        await validation_service.validate(
            db=db,
            dataset_version_id=data.dataset_version_id,
            evaluation_type=data.evaluation_type.value,
            configuration=data.configuration or {},
        )

        # --------------------------------------------------------------
        # Create evaluation run
        # --------------------------------------------------------------

        evaluation_run = EvaluationRun(
            dataset_version_id=data.dataset_version_id,
            model_id=data.model_id,
            name=data.name,
            status=EvaluationRunStatus.PENDING,
            evaluation_type=data.evaluation_type,
            configuration=data.configuration,
            total_cases=dataset_version.case_count,
            completed_cases=0,
            failed_cases=0,
            is_active=True,
        )

        db.add(evaluation_run)

        if commit:
            await db.commit()
            await db.refresh(evaluation_run)

        return evaluation_run

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        run_id: UUID,
    ) -> EvaluationRun | None:
        result = await db.execute(
            select(EvaluationRun).where(
                EvaluationRun.id == run_id,
                EvaluationRun.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_status(
        db: AsyncSession,
        run_id: UUID,
    ) -> dict | None:
        run = await EvaluationRunService.get_by_id(
            db,
            run_id,
        )

        if run is None:
            return None

        processed_cases = run.completed_cases + run.failed_cases + run.not_applicable_cases

        progress_percent = (processed_cases / run.total_cases) * 100 if run.total_cases > 0 else 0.0

        return {
            "id": run.id,
            "status": run.status,
            "total_cases": run.total_cases,
            "completed_cases": run.completed_cases,
            "failed_cases": run.failed_cases,
            "not_applicable_cases": run.not_applicable_cases,
            "processed_cases": processed_cases,
            "progress_percent": progress_percent,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "duration_ms": run.duration_ms,
        }

    @staticmethod
    async def list(
        db: AsyncSession,
        dataset_version_id: UUID | None = None,
        model_id: UUID | None = None,
    ) -> list[EvaluationRun]:
        query = select(EvaluationRun).where(EvaluationRun.is_active.is_(True))

        if dataset_version_id is not None:
            query = query.where(EvaluationRun.dataset_version_id == dataset_version_id)

        if model_id is not None:
            query = query.where(EvaluationRun.model_id == model_id)

        query = query.order_by(EvaluationRun.created_at.desc())

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        run: EvaluationRun,
        data: EvaluationRunUpdate,
    ) -> EvaluationRun:

        if not run.is_active:
            raise ValueError("Evaluation run is inactive")

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if "status" in update_data:
            EvaluationRunService.validate_status_transition(
                run.status,
                update_data["status"],
            )

        for field, value in update_data.items():
            setattr(run, field, value)

        await db.commit()
        await db.refresh(run)

        return run

    @staticmethod
    async def delete(
        db: AsyncSession,
        run: EvaluationRun,
    ) -> None:
        if not run.is_active:
            raise ValueError("Evaluation run is already inactive")

        run.is_active = False
        await db.commit()

    @staticmethod
    async def claim_pending(
        db: AsyncSession,
        run_id: UUID,
    ) -> EvaluationRun | None:
        result = await db.execute(
            update(EvaluationRun)
            .where(
                EvaluationRun.id == run_id,
                EvaluationRun.status == EvaluationRunStatus.PENDING,
                EvaluationRun.is_active.is_(True),
            )
            .values(
                status=EvaluationRunStatus.RUNNING,
            )
        )

        if result.rowcount != 1:
            return None

        await db.commit()

        return await EvaluationRunService.get_by_id(
            db,
            run_id,
        )

    @staticmethod
    async def get_running_for_recovery(
        db: AsyncSession,
        run_id: UUID,
    ) -> EvaluationRun | None:
        """
        Return an active RUNNING evaluation run for recovery.

        Recovery does not perform a status transition.
        Redis determines that the queue message is stale,
        while PostgreSQL remains the source of truth for
        whether the run is still recoverable.
        """
        result = await db.execute(
            select(EvaluationRun).where(
                EvaluationRun.id == run_id,
                EvaluationRun.status == EvaluationRunStatus.RUNNING,
                EvaluationRun.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()
