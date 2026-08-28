import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationResult
from app.schemas.evaluation.summary import (
    EvaluationFeedbackSummary,
    EvaluationSummary,
)
from app.services.evaluation_engine.feedback_aggregation import (
    EvaluationFeedbackAggregationService,
)
from app.services.evaluation_engine.scoring_config import (
    ScoringConfigurationService,
)
from app.services.model_gateway import ModelGateway


class LLMEvaluationSummaryService:
    """
    Generates the final structured evaluation summary.

    Responsibilities:

    1. Read case-level evaluation results from PostgreSQL.
    2. Resolve scoring configuration using Redis-backed caching.
    3. Resolve aggregated feedback from Redis.
    4. Calculate deterministic metric averages.
    5. Calculate deterministic weighted overall score.
    6. Send the evaluation evidence to an LLM judge.
    7. Validate the structured LLM response.
    8. Return a final EvaluationSummary.

    PostgreSQL:
        Source of truth.

    Redis:
        Reusable working/cache layer.

    LLM:
        Generates qualitative feedback only.
    """

    def __init__(
        self,
        redis: Redis | None,
        model_gateway: ModelGateway,
        *,
        judge_model: str = "llama3.2:3b",
        judge_provider: str = "ollama",
        judge_base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.redis = redis
        self.model_gateway = model_gateway

        self.judge_model = judge_model
        self.judge_provider = judge_provider
        self.judge_base_url = judge_base_url
        self.timeout = timeout

        self.feedback_aggregation = (
            EvaluationFeedbackAggregationService(redis) if redis is not None else None
        )

        self.scoring_configuration = ScoringConfigurationService(
            redis=redis,
        )

    async def generate(
        self,
        db: AsyncSession,
        evaluation_run_id: UUID,
    ) -> EvaluationSummary:
        """
        Generate the final evaluation summary.
        """

        results = await self._load_results(
            db,
            evaluation_run_id,
        )

        metrics = self._calculate_metrics(results)

        scoring_configuration = await self.scoring_configuration.get(
            db,
            evaluation_run_id,
        )

        overall_score = self._calculate_overall_score(
            metrics,
            scoring_configuration,
        )

        feedback = await self._get_feedback(
            db,
            evaluation_run_id,
            results,
        )

        llm_feedback = await self._generate_llm_feedback(
            evaluation_run_id=evaluation_run_id,
            overall_score=overall_score,
            metrics=metrics,
            feedback=feedback,
        )

        return EvaluationSummary(
            overall_score=overall_score,
            metrics=metrics,
            feedback=llm_feedback,
            metadata={
                "summary_model": self.judge_model,
                "summary_provider": self.judge_provider,
            },
        )

    async def _load_results(
        self,
        db: AsyncSession,
        evaluation_run_id: UUID,
    ) -> list[EvaluationResult]:

        result = await db.execute(
            select(EvaluationResult).where(
                EvaluationResult.evaluation_run_id == evaluation_run_id,
                EvaluationResult.is_active.is_(True),
                EvaluationResult.status == "completed",
            )
        )

        return list(result.scalars().all())

    @staticmethod
    def _calculate_metrics(
        results: list[EvaluationResult],
    ) -> dict[str, float]:
        """
        Calculate deterministic average score per metric.
        """

        totals: dict[str, float] = {}
        counts: dict[str, int] = {}

        for result in results:
            scores = result.scores

            if not isinstance(scores, dict):
                continue

            for metric, value in scores.items():
                if not isinstance(value, dict):
                    continue

                score = value.get("score")

                if isinstance(score, bool):
                    continue

                if not isinstance(score, (int, float)):
                    continue

                totals[metric] = totals.get(metric, 0.0) + float(score)

                counts[metric] = counts.get(metric, 0) + 1

        return {metric: totals[metric] / counts[metric] for metric in totals if counts[metric] > 0}

    @staticmethod
    def _calculate_overall_score(
        metrics: dict[str, float],
        scoring_configuration: dict[str, Any],
    ) -> float:
        """
        Calculate deterministic weighted overall score.

        Supports:

        {
            "weights": {
                "relevance": 0.3,
                "faithfulness": 0.3,
                "f1": 0.2,
                "llm_judge": 0.2
            }
        }
        """

        weights = scoring_configuration.get(
            "weights",
            {},
        )

        if not isinstance(weights, dict):
            weights = {}

        weighted_score = 0.0
        total_weight = 0.0

        for metric, score in metrics.items():
            weight = weights.get(metric)

            if weight is None:
                continue

            if not isinstance(weight, (int, float)):
                continue

            if weight <= 0:
                continue

            weighted_score += score * float(weight)
            total_weight += float(weight)

        if total_weight == 0:
            if not metrics:
                return 0.0

            return sum(metrics.values()) / len(metrics)

        return weighted_score / total_weight

    async def _get_feedback(
        self,
        db: AsyncSession,
        evaluation_run_id: UUID,
        results: list[EvaluationResult],
    ) -> list[str]:

        if self.feedback_aggregation is None:
            return self._extract_feedback(results)

        aggregation = await self.feedback_aggregation.aggregate(
            db,
            evaluation_run_id,
        )

        feedback_items: list[str] = []

        for key in aggregation.get("chunks", []):
            try:
                cached = await self.redis.get(key)

                if cached is None:
                    continue

                if isinstance(cached, bytes):
                    cached = cached.decode("utf-8")

                payload = json.loads(cached)

                items = payload.get("items", [])

                if isinstance(items, list):
                    feedback_items.extend(item for item in items if isinstance(item, str))

            except Exception:
                continue

        return feedback_items

    @staticmethod
    def _extract_feedback(
        results: list[EvaluationResult],
    ) -> list[str]:

        feedback: list[str] = []

        for result in results:
            if isinstance(result.feedback, str):
                value = result.feedback.strip()

                if value:
                    feedback.append(value)

        return feedback

    async def _generate_llm_feedback(
        self,
        *,
        evaluation_run_id: UUID,
        overall_score: float,
        metrics: dict[str, float],
        feedback: list[str],
    ) -> EvaluationFeedbackSummary:

        prompt = self._build_summary_prompt(
            evaluation_run_id=evaluation_run_id,
            overall_score=overall_score,
            metrics=metrics,
            feedback=feedback,
        )

        configuration: dict[str, Any] = {
            "model": self.judge_model,
            "timeout": self.timeout,
            "response_format": "json",
        }

        if self.judge_base_url is not None:
            configuration["base_url"] = self.judge_base_url

        response = await self.model_gateway.generate(
            prompt=prompt,
            configuration=configuration,
        )

        return self._parse_llm_feedback(
            response.output,
        )

    @staticmethod
    def _build_summary_prompt(
        *,
        evaluation_run_id: UUID,
        overall_score: float,
        metrics: dict[str, float],
        feedback: list[str],
    ) -> str:

        metrics_json = json.dumps(
            metrics,
            ensure_ascii=False,
            indent=2,
        )

        feedback_json = json.dumps(
            feedback,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
You are the final evaluation analysis judge.

Your task is to summarize the results of an AI evaluation run.

The numerical evaluation scores have already been calculated
deterministically. DO NOT modify or recalculate them.

Evaluation run:
{evaluation_run_id}

Overall score:
{overall_score:.6f}

Metrics:
{metrics_json}

Collected evaluator feedback:
{feedback_json}

Generate qualitative analysis only.

Return ONLY valid JSON with exactly this structure:

{{
  "overall": "overall assessment",
  "strengths": [
    "strength"
  ],
  "weaknesses": [
    "weakness"
  ],
  "patterns": [
    "recurring pattern"
  ],
  "recommendations": [
    "recommendation"
  ]
}}

Rules:

- Do not invent metrics.
- Do not change the overall score.
- Base observations on the supplied metrics and feedback.
- Identify recurring patterns when possible.
- Strengths should describe demonstrated strengths.
- Weaknesses should describe observed problems.
- Recommendations should be actionable.
- Return JSON only.
""".strip()

    @staticmethod
    def _parse_llm_feedback(
        raw_output: str,
    ) -> EvaluationFeedbackSummary:

        if not raw_output or not raw_output.strip():
            raise ValueError("Summary LLM returned an empty response.")

        cleaned = raw_output.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise ValueError("Summary LLM returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("Summary LLM response must be a JSON object.")

        return EvaluationFeedbackSummary(
            overall=str(data.get("overall", "")),
            strengths=LLMEvaluationSummaryService._normalize_list(
                data.get("strengths"),
            ),
            weaknesses=LLMEvaluationSummaryService._normalize_list(
                data.get("weaknesses"),
            ),
            patterns=LLMEvaluationSummaryService._normalize_list(
                data.get("patterns"),
            ),
            recommendations=LLMEvaluationSummaryService._normalize_list(
                data.get("recommendations"),
            ),
        )

    @staticmethod
    def _normalize_list(
        value: Any,
    ) -> list[str]:

        if not isinstance(value, list):
            return []

        return [str(item).strip() for item in value if str(item).strip()]
