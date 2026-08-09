from typing import Any

from app.services.scoring.base import (
    ScoreCalculationResult,
    ScoreCalculator,
)


class WeightedScoreCalculator(ScoreCalculator):
    @property
    def name(self) -> str:
        return "weighted"

    def calculate(
        self,
        *,
        scores: dict[str, dict[str, Any]],
        configuration: dict[str, Any] | None = None,
    ) -> ScoreCalculationResult:

        if not scores:
            return ScoreCalculationResult(
                score=0.0,
                metadata={
                    "weights": {},
                },
            )

        configuration = configuration or {}

        configured_weights = configuration.get("weights")

        if configured_weights is not None:
            if not isinstance(configured_weights, dict):
                raise ValueError(
                    "'weights' must be an object mapping "
                    "evaluator names to numeric weights."
                )
        else:
            configured_weights = {}

        evaluator_names = list(scores.keys())

        validated_weights: dict[str, float] = {}

        for evaluator_name in evaluator_names:
            weight = configured_weights.get(
                evaluator_name,
                1.0,
            )

            if not isinstance(weight, (int, float)):
                raise ValueError(
                    f"Weight for evaluator "
                    f"'{evaluator_name}' must be numeric."
                )

            if weight < 0:
                raise ValueError(
                    f"Weight for evaluator "
                    f"'{evaluator_name}' cannot be negative."
                )

            validated_weights[evaluator_name] = float(weight)

        total_weight = sum(validated_weights.values())

        if total_weight <= 0:
            raise ValueError(
                "At least one evaluator weight must be "
                "greater than zero."
            )

        normalized_weights = {
            evaluator_name: weight / total_weight
            for evaluator_name, weight in validated_weights.items()
        }

        overall_score = sum(
            float(scores[evaluator_name]["score"])
            * normalized_weights[evaluator_name]
            for evaluator_name in evaluator_names
        )

        return ScoreCalculationResult(
            score=overall_score,
            metadata={
                "weights": normalized_weights,
            },
        )