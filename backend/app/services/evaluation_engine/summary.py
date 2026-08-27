from statistics import quantiles
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun
from app.models.evaluation_result import EvaluationResult
from app.models.model import Model
from app.services.evaluation_engine.cost import EvaluationCostService


class EvaluationRunSummaryService:
    """
    Aggregates evaluation results into a run-level summary.
    """

    @staticmethod
    async def calculate(
        db: AsyncSession,
        evaluation_run_id,
    ) -> dict[str, Any]:
        run_result = await db.execute(
            select(EvaluationRun).where(
                EvaluationRun.id == evaluation_run_id,
                EvaluationRun.is_active.is_(True),
            )
        )

        run = run_result.scalar_one_or_none()

        if run is None:
            return {
                "overall_score": 0.0,
                "metrics": {},
                "total_results": 0,
                "completed_cases": 0,
                "failed_cases": 0,
                "model": None,
                "performance": {
                    "duration_ms": None,
                    "total_model_latency_ms": 0,
                    "avg_model_latency_ms": None,
                    "min_model_latency_ms": None,
                    "p50_model_latency_ms": None,
                    "p95_model_latency_ms": None,
                    "p99_model_latency_ms": None,
                    "max_model_latency_ms": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "throughput_cases_per_second": None,
                    "cost": EvaluationCostService.calculate(
                        input_tokens=0,
                        output_tokens=0,
                    ),
                },
            }

        # --------------------------------------------------------------
        # Model pricing
        # --------------------------------------------------------------

        model_result = await db.execute(
            select(Model).where(
                Model.id == run.model_id,
                Model.is_active.is_(True),
            )
        )

        model = model_result.scalar_one_or_none()

        model_summary = None

        if model is not None:
            model_summary = {
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "model_identifier": model.model_identifier,
            }

        input_price_per_million = model.input_price_per_million if model else 0.0

        output_price_per_million = model.output_price_per_million if model else 0.0

        pricing_currency = (
            model.pricing_currency if model else EvaluationCostService.DEFAULT_CURRENCY
        )

        # --------------------------------------------------------------
        # Evaluation results
        # --------------------------------------------------------------

        result = await db.execute(
            select(EvaluationResult).where(
                EvaluationResult.evaluation_run_id == evaluation_run_id,
                EvaluationResult.is_active.is_(True),
            )
        )

        results = result.scalars().all()

        completed_results = [item for item in results if item.status == "completed"]

        failed_results = [item for item in results if item.status == "failed"]

        # --------------------------------------------------------------
        # Evaluation metrics
        # --------------------------------------------------------------

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

                metric_totals[metric_name] = metric_totals.get(metric_name, 0.0) + score

                metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1

        metrics = {
            metric_name: metric_totals[metric_name] / metric_counts[metric_name]
            for metric_name in metric_totals
            if metric_counts[metric_name] > 0
        }

        overall_score = overall_total / overall_count if overall_count > 0 else 0.0

        # --------------------------------------------------------------
        # Run-level performance metrics
        # --------------------------------------------------------------

        latencies = [
            result.latency_ms for result in completed_results if result.latency_ms is not None
        ]

        total_model_latency_ms = sum(latencies)

        avg_model_latency_ms = total_model_latency_ms / len(latencies) if latencies else None

        min_model_latency_ms = min(latencies) if latencies else None

        max_model_latency_ms = max(latencies) if latencies else None

        p50_model_latency_ms = None
        p95_model_latency_ms = None
        p99_model_latency_ms = None

        if latencies:
            if len(latencies) == 1:
                p50_model_latency_ms = float(latencies[0])
                p95_model_latency_ms = float(latencies[0])
                p99_model_latency_ms = float(latencies[0])
            else:
                percentile_values = quantiles(
                    latencies,
                    n=100,
                    method="inclusive",
                )

                p50_model_latency_ms = percentile_values[49]
                p95_model_latency_ms = percentile_values[94]
                p99_model_latency_ms = percentile_values[98]

        input_tokens = sum(result.input_tokens or 0 for result in completed_results)

        output_tokens = sum(result.output_tokens or 0 for result in completed_results)

        total_tokens = sum(result.total_tokens or 0 for result in completed_results)

        # --------------------------------------------------------------
        # Cost
        # --------------------------------------------------------------

        cost = EvaluationCostService.calculate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_price_per_million=input_price_per_million,
            output_price_per_million=output_price_per_million,
            currency=pricing_currency,
        )

        # --------------------------------------------------------------
        # Throughput
        # --------------------------------------------------------------

        throughput_cases_per_second = None

        if run.duration_ms and run.duration_ms > 0:
            throughput_cases_per_second = len(completed_results) / (run.duration_ms / 1000)

        performance = {
            "duration_ms": run.duration_ms,
            "total_model_latency_ms": total_model_latency_ms,
            "avg_model_latency_ms": avg_model_latency_ms,
            "min_model_latency_ms": min_model_latency_ms,
            "p50_model_latency_ms": p50_model_latency_ms,
            "p95_model_latency_ms": p95_model_latency_ms,
            "p99_model_latency_ms": p99_model_latency_ms,
            "max_model_latency_ms": max_model_latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "throughput_cases_per_second": throughput_cases_per_second,
            "cost": cost,
        }

        return {
            "model": model_summary,
            "overall_score": overall_score,
            "metrics": metrics,
            "total_results": len(results),
            "completed_cases": len(completed_results),
            "failed_cases": len(failed_results),
            "performance": performance,
        }
