from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation_result import EvaluationResult


class EvaluationRunSummaryService:
    """
    Aggregates evaluation results into a run-level summary.
    """

    @staticmethod
    async def calculate(
        db: AsyncSession,
        evaluation_run_id,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(EvaluationResult).where(
                EvaluationResult.evaluation_run_id
                == evaluation_run_id,
                EvaluationResult.is_active.is_(True),
            )
        )

        results = result.scalars().all()

        completed_results = [
            item
            for item in results
            if item.status == "completed"
        ]

        failed_results = [
            item
            for item in results
            if item.status == "failed"
        ]

        metric_totals: dict[str, float] = {}
        metric_counts: dict[str, int] = {}

        overall_total = 0.0
        overall_count = 0

        for result in completed_results:
            scores = result.scores or {}

            for metric_name, metric_data in scores.items():
                if not isinstance(metric_data, dict):
                    continue

                score = metric_data.get("score")

                if not isinstance(score, (int, float)):
                    continue

                score = float(score)

                if metric_name == "overall":
                    overall_total += score
                    overall_count += 1
                    continue

                metric_totals[metric_name] = (
                    metric_totals.get(metric_name, 0.0)
                    + score
                )

                metric_counts[metric_name] = (
                    metric_counts.get(metric_name, 0)
                    + 1
                )

        metrics = {
            metric_name: metric_totals[metric_name]
            / metric_counts[metric_name]
            for metric_name in metric_totals
            if metric_counts[metric_name] > 0
        }

        overall_score = (
            overall_total / overall_count
            if overall_count > 0
            else 0.0
        )

        return {
            "overall_score": overall_score,
            "metrics": metrics,
            "total_results": len(results),
            "completed_cases": len(completed_results),
            "failed_cases": len(failed_results),
        }