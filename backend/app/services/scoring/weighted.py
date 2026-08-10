from math import isfinite
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
                    "strategy": self.name,
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

        validated_scores: dict[str, float] = {}
        validated_weights: dict[str, float] = {}

        for evaluator_name, evaluator_result in scores.items():

            if evaluator_name == "overall":
                raise ValueError(
                    "'overall' must not be included in evaluator scores."
                )

            if not isinstance(evaluator_result, dict):
                raise ValueError(
                    f"Score for evaluator '{evaluator_name}' "
                    "must be an object."
                )

            if "score" not in evaluator_result:
                raise ValueError(
                    f"Evaluator '{evaluator_name}' "
                    "is missing a 'score'."
                )

            score = evaluator_result["score"]

            if not isinstance(score, (int, float)):
                raise ValueError(
                    f"Score for evaluator '{evaluator_name}' "
                    "must be numeric."
                )

            score = float(score)

            if not isfinite(score):
                raise ValueError(
                    f"Score for evaluator '{evaluator_name}' "
                    "must be finite."
                )

            if score < 0.0 or score > 1.0:
                raise ValueError(
                    f"Score for evaluator '{evaluator_name}' "
                    "must be between 0.0 and 1.0."
                )

            validated_scores[evaluator_name] = score

            weight = configured_weights.get(
                evaluator_name,
                1.0,
            )

            if not isinstance(weight, (int, float)):
                raise ValueError(
                    f"Weight for evaluator "
                    f"'{evaluator_name}' must be numeric."
                )

            weight = float(weight)

            if not isfinite(weight):
                raise ValueError(
                    f"Weight for evaluator "
                    f"'{evaluator_name}' must be finite."
                )

            if weight < 0:
                raise ValueError(
                    f"Weight for evaluator "
                    f"'{evaluator_name}' cannot be negative."
                )

            validated_weights[evaluator_name] = weight

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
            validated_scores[evaluator_name]
            * normalized_weights[evaluator_name]
            for evaluator_name in validated_scores
        )

        return ScoreCalculationResult(
            score=overall_score,
            metadata={
                "strategy": self.name,
                "weights": normalized_weights,
            },
        )