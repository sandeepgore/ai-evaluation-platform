from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model.evaluation_summary import EvaluationSummary


class EvaluationSummaryPersistenceService:
    """
    Persists and retrieves evaluation run summaries.

    PostgreSQL is the source of truth.
    Redis is used only as a cache above this service.
    """

    @staticmethod
    async def get(
        db: AsyncSession,
        evaluation_run_id: UUID,
    ) -> EvaluationSummary | None:
        result = await db.execute(
            select(EvaluationSummary).where(
                EvaluationSummary.evaluation_run_id == evaluation_run_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def save(
        db: AsyncSession,
        evaluation_run_id: UUID,
        summary: dict[str, Any],
    ) -> EvaluationSummary:
        """
        Create or update the persisted summary for an evaluation run.

        There is exactly one summary per evaluation run.
        """

        existing = await EvaluationSummaryPersistenceService.get(
            db,
            evaluation_run_id,
        )

        if existing is None:
            existing = EvaluationSummary(
                evaluation_run_id=evaluation_run_id,
            )
            db.add(existing)

        existing.overall_score = float(summary.get("overall_score", 0.0))

        existing.metrics = summary.get(
            "metrics",
            {},
        )

        existing.performance = summary.get(
            "performance",
            {},
        )

        existing.feedback = summary.get(
            "feedback",
            {},
        )

        existing.summary_metadata = summary.get(
            "metadata",
            {},
        )

        await db.flush()

        return existing

    @staticmethod
    async def delete(
        db: AsyncSession,
        evaluation_run_id: UUID,
    ) -> None:
        existing = await EvaluationSummaryPersistenceService.get(
            db,
            evaluation_run_id,
        )

        if existing is None:
            return

        await db.delete(existing)
        await db.flush()
