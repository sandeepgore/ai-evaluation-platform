from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_version import DatasetVersion
from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.model import Model
from app.schemas.evaluation import EvaluationRunCreate, EvaluationRunUpdate


class EvaluationRunService:
    @staticmethod
    async def create(
        db: AsyncSession,
        data: EvaluationRunCreate,
    ) -> EvaluationRun:
        # Verify dataset version exists
        dataset_version_result = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == data.dataset_version_id
            )
        )
        dataset_version = dataset_version_result.scalar_one_or_none()

        if dataset_version is None:
            raise ValueError("Dataset version not found")

        # Verify model exists
        model_result = await db.execute(
            select(Model).where(Model.id == data.model_id)
        )
        model = model_result.scalar_one_or_none()

        if model is None:
            raise ValueError("Model not found")

        evaluation_run = EvaluationRun(
            dataset_version_id=data.dataset_version_id,
            model_id=data.model_id,
            name=data.name,
            status=EvaluationRunStatus.PENDING,
            configuration=data.configuration,
            summary_feedback=None,
            total_cases=dataset_version.case_count,
            completed_cases=0,
            failed_cases=0,
            is_active=True,
        )

        db.add(evaluation_run)
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
                EvaluationRun.id == run_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        dataset_version_id: UUID | None = None,
        model_id: UUID | None = None,
    ) -> list[EvaluationRun]:
        query = select(EvaluationRun)

        if dataset_version_id is not None:
            query = query.where(
                EvaluationRun.dataset_version_id == dataset_version_id
            )

        if model_id is not None:
            query = query.where(
                EvaluationRun.model_id == model_id
            )

        query = query.order_by(EvaluationRun.created_at.desc())

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        run: EvaluationRun,
        data: EvaluationRunUpdate,
    ) -> EvaluationRun:
        update_data = data.model_dump(exclude_unset=True)

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
        await db.delete(run)
        await db.commit()