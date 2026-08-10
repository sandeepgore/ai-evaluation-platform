from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EvaluationResult
from app.schemas.evaluation_results import (
    EvaluationResultListResponse,
    EvaluationResultResponse,
)


class EvaluationResultService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        evaluation_run_id: UUID,
        dataset_case_id: UUID,
        status: str = "pending",
        actual_output: str | None = None,
        expected_output: str | None = None,
        scores: dict | None = None,
        feedback: str | None = None,
        trace: dict | None = None,
        latency_ms: int | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        error_message: str | None = None,
    ) -> EvaluationResult:
        result = EvaluationResult(
            evaluation_run_id=evaluation_run_id,
            dataset_case_id=dataset_case_id,
            status=status,
            actual_output=actual_output,
            expected_output=expected_output,
            scores=scores,
            feedback=feedback,
            trace=trace,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            error_message=error_message,
        )

        db.add(result)
        await db.commit()
        await db.refresh(result)

        return result

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        result_id: UUID,
    ) -> EvaluationResult | None:
        result = await db.get(EvaluationResult, result_id)
        return result

    @staticmethod
    async def update(
        db: AsyncSession,
        result: EvaluationResult,
        **fields,
    ) -> EvaluationResult:
        for field, value in fields.items():
            if value is not None and hasattr(result, field):
                setattr(result, field, value)

        await db.commit()
        await db.refresh(result)

        return result

    @staticmethod
    async def delete(
        db: AsyncSession,
        result: EvaluationResult,
    ) -> None:
        result.is_active = False

        await db.commit()

    @staticmethod
    async def get_run_statistics(
        db: AsyncSession,
        evaluation_run_id: UUID,
    ) -> dict:
        query = select(
            func.count(EvaluationResult.id).label("total"),
            func.count(EvaluationResult.id)
            .filter(EvaluationResult.status == "completed")
            .label("completed"),
            func.count(EvaluationResult.id)
            .filter(EvaluationResult.status == "failed")
            .label("failed"),
            func.count(EvaluationResult.id)
            .filter(EvaluationResult.status == "pending")
            .label("pending"),
        ).where(
            EvaluationResult.evaluation_run_id == evaluation_run_id,
            EvaluationResult.is_active.is_(True),
        )

        result = await db.execute(query)
        row = result.one()

        return {
            "total": row.total,
            "completed": row.completed,
            "failed": row.failed,
            "pending": row.pending,
        }

    @staticmethod
    async def list_by_run(
        db: AsyncSession,
        evaluation_run_id: UUID,
        *,
        status_filter: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> EvaluationResultListResponse:
        conditions = [
            EvaluationResult.evaluation_run_id == evaluation_run_id,
            EvaluationResult.is_active.is_(True),
        ]

        if status_filter is not None:
            conditions.append(EvaluationResult.status == status_filter)

        total_query = select(func.count(EvaluationResult.id)).where(*conditions)

        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(EvaluationResult)
            .where(*conditions)
            .order_by(EvaluationResult.created_at.asc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        items = result.scalars().all()

        return EvaluationResultListResponse(
            items=[EvaluationResultResponse.model_validate(item) for item in items],
            total=total,
        )
