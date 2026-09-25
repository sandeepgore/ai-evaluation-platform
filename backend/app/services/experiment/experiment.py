from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment.experiment import Experiment
from app.models.experiment.experiment_snapshot import ExperimentSnapshot
from app.schemas.experiment.experiment import ExperimentCreate
from app.schemas.experiment.snapshot import ExperimentSnapshotCreate
from app.services.evaluation.evaluation import EvaluationRunService
from app.services.evaluation_engine.summary_persistence import (
    EvaluationSummaryPersistenceService,
)


class ExperimentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ExperimentCreate) -> Experiment:
        experiment = Experiment(
            name=data.name,
            description=data.description,
        )

        self.db.add(experiment)
        await self.db.commit()
        await self.db.refresh(experiment)

        return experiment

    async def get_by_id(
        self,
        experiment_id: UUID,
    ) -> Experiment | None:
        result = await self.db.execute(
            select(Experiment).where(
                Experiment.id == experiment_id,
                Experiment.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        scope: str = "recent",
    ) -> list[Experiment]:
        if scope not in {"recent", "all"}:
            raise ValueError("Invalid experiment scope. Expected 'recent' or 'all'.")

        query = select(Experiment).where(
            Experiment.is_active.is_(True),
        )

        if scope == "recent":
            query = query.where(Experiment.created_at >= func.now() - text("interval '3 months'"))

        query = query.order_by(Experiment.created_at.desc())

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def delete(self, experiment: Experiment) -> None:
        experiment.is_active = False

        await self.db.commit()

    async def create_snapshot(
        self,
        experiment: Experiment,
        data: ExperimentSnapshotCreate,
    ) -> ExperimentSnapshot:
        run_results: dict[str, dict] = {}

        for run_id in data.run_ids:
            run = await EvaluationRunService.get_by_id(
                self.db,
                run_id,
            )

            if run is None:
                raise ValueError("Evaluation run not found")

            # Experiment consumes the persisted evaluation summary.
            # It does not recalculate the evaluation.
            summary = await EvaluationSummaryPersistenceService.get(
                self.db,
                run_id,
            )

            if summary is None:
                raise ValueError("Evaluation summary not found")

            # Selected experiment runs are expected to be completed.
            run_status = run.status.value if hasattr(run.status, "value") else run.status

            if run_status != "completed":
                raise ValueError("Evaluation run must be completed")

            run_results[str(run_id)] = {
                "run": {
                    "name": run.name,
                    "model_id": str(run.model_id),
                    "dataset_version_id": str(run.dataset_version_id),
                    "status": run_status,
                    "total_cases": run.total_cases,
                    "completed_cases": run.completed_cases,
                    "failed_cases": run.failed_cases,
                    "duration_ms": run.duration_ms,
                },
                "summary": {
                    "overall_score": summary.overall_score,
                    "metrics": summary.metrics,
                    "performance": summary.performance,
                    "feedback": summary.feedback,
                    "summary_metadata": summary.summary_metadata,
                },
            }

        comparison = self._build_snapshot_comparison(
            data.run_ids,
            run_results,
        )

        snapshot = ExperimentSnapshot(
            experiment_id=experiment.id,
            run_ids=[str(run_id) for run_id in data.run_ids],
            run_results=run_results,
            comparison=comparison,
            calculation_version=1,
        )

        self.db.add(snapshot)

        await self.db.commit()
        await self.db.refresh(snapshot)

        return snapshot

    @staticmethod
    def _build_snapshot_comparison(
        run_ids: list[UUID],
        run_results: dict[str, dict],
    ) -> dict[str, dict]:
        if len(run_ids) < 2:
            return {}

        baseline_id = str(run_ids[0])
        candidate_id = str(run_ids[1])

        baseline_result = run_results[baseline_id]
        candidate_result = run_results[candidate_id]

        baseline_run = baseline_result["run"]
        candidate_run = candidate_result["run"]

        baseline_summary = baseline_result["summary"]
        candidate_summary = candidate_result["summary"]

        comparison: dict[str, dict] = {}

        # --------------------------------------------------------------
        # Overall score
        # --------------------------------------------------------------

        baseline_overall = baseline_summary["overall_score"]
        candidate_overall = candidate_summary["overall_score"]

        comparison["overall_score"] = {
            "baseline": baseline_overall,
            "candidate": candidate_overall,
            "delta": candidate_overall - baseline_overall,
        }

        # --------------------------------------------------------------
        # Quality metrics
        # --------------------------------------------------------------

        baseline_metrics = baseline_summary.get("metrics", {})
        candidate_metrics = candidate_summary.get("metrics", {})

        for metric_name in set(baseline_metrics) & set(candidate_metrics):
            baseline_value = baseline_metrics[metric_name]
            candidate_value = candidate_metrics[metric_name]

            comparison[metric_name] = {
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": candidate_value - baseline_value,
            }

        # --------------------------------------------------------------
        # Execution / case statistics
        # --------------------------------------------------------------

        comparison["execution"] = {}

        execution_fields = [
            "total_cases",
            "completed_cases",
            "failed_cases",
        ]

        for field in execution_fields:
            baseline_value = baseline_run.get(field)
            candidate_value = candidate_run.get(field)

            if baseline_value is None or candidate_value is None:
                continue

            comparison["execution"][field] = {
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": candidate_value - baseline_value,
            }

        # --------------------------------------------------------------
        # Performance
        # --------------------------------------------------------------

        baseline_performance = baseline_summary.get("performance", {})
        candidate_performance = candidate_summary.get("performance", {})

        performance_fields = [
            "duration_ms",
            "avg_model_latency_ms",
            "p50_model_latency_ms",
            "p95_model_latency_ms",
            "p99_model_latency_ms",
            "min_model_latency_ms",
            "max_model_latency_ms",
            "total_model_latency_ms",
            "throughput_cases_per_second",
        ]

        comparison["performance"] = {}

        for field in performance_fields:
            baseline_value = baseline_performance.get(field)
            candidate_value = candidate_performance.get(field)

            if baseline_value is None or candidate_value is None:
                continue

            comparison["performance"][field] = {
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": candidate_value - baseline_value,
            }

        # --------------------------------------------------------------
        # Token usage
        # --------------------------------------------------------------

        token_fields = [
            "input_tokens",
            "output_tokens",
            "total_tokens",
        ]

        comparison["tokens"] = {}

        for field in token_fields:
            baseline_value = baseline_performance.get(field)
            candidate_value = candidate_performance.get(field)

            if baseline_value is None or candidate_value is None:
                continue

            comparison["tokens"][field] = {
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": candidate_value - baseline_value,
            }

        # --------------------------------------------------------------
        # Cost
        # --------------------------------------------------------------

        baseline_cost = baseline_performance.get("cost", {})
        candidate_cost = candidate_performance.get("cost", {})

        cost_fields = [
            "input_cost",
            "output_cost",
            "total_cost",
        ]

        comparison["cost"] = {
            "currency": baseline_cost.get("currency"),
        }

        for field in cost_fields:
            baseline_value = baseline_cost.get(field)
            candidate_value = candidate_cost.get(field)

            if baseline_value is None or candidate_value is None:
                continue

            comparison["cost"][field] = {
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": candidate_value - baseline_value,
            }

        # --------------------------------------------------------------
        # Qualitative feedback
        # --------------------------------------------------------------

        baseline_feedback = baseline_summary.get("feedback", {})
        candidate_feedback = candidate_summary.get("feedback", {})

        feedback_fields = [
            "strengths",
            "weaknesses",
            "patterns",
            "recommendations",
            "evaluator_feedback",
        ]

        comparison["feedback"] = {}

        for field in feedback_fields:
            baseline_value = baseline_feedback.get(field)
            candidate_value = candidate_feedback.get(field)

            if baseline_value is None and candidate_value is None:
                continue

            comparison["feedback"][field] = {
                "baseline": baseline_value,
                "candidate": candidate_value,
            }

        return comparison

    async def get_snapshot(
        self,
        experiment_id: UUID,
        snapshot_id: UUID,
    ) -> ExperimentSnapshot | None:
        result = await self.db.execute(
            select(ExperimentSnapshot).where(
                ExperimentSnapshot.id == snapshot_id,
                ExperimentSnapshot.experiment_id == experiment_id,
            )
        )

        return result.scalar_one_or_none()
