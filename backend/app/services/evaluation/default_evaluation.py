from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.services.evaluation.dataset_capability import (
    DatasetCapabilities,
)


class DefaultDataPolicy(str, Enum):
    """
    Determines how strictly required dataset data must be
    available before an evaluator is selected.
    """

    STRICT = "strict"
    PARTIAL = "partial"
    THRESHOLD = "threshold"


@dataclass(frozen=True)
class DefaultEvaluationPlan:
    """
    Resolved default evaluation configuration.

    This represents the result of the default-evaluation
    decision process. It does not execute evaluators.
    """

    evaluators: tuple[str, ...]

    data_policy: DefaultDataPolicy

    threshold: float | None

    warnings: tuple[str, ...]

    reasons: dict[str, str]


class DefaultEvaluationPolicy:
    """
    Determines which evaluators should be selected by default.

    The policy considers:

        - evaluation type
        - dataset capabilities
        - evaluator data requirements
        - data availability policy

    This class does not:
        - execute evaluators
        - access SQLAlchemy
        - access FastAPI
        - modify EvaluationEngine
    """

    DEFAULT_THRESHOLD = 0.95

    # --------------------------------------------------------------
    # Default evaluator candidates
    #
    # These are candidates, NOT unconditional selections.
    # Actual selection depends on dataset capabilities.
    # --------------------------------------------------------------

    DEFAULT_EVALUATORS = {
        "text": (
            "exact_match",
            "contains",
            "f1",
            "rouge_l",
            "bleu",
        ),
        "rag": (
            "exact_match",
            "contains",
            "f1",
            "rouge_l",
            "bleu",
            "relevance",
            "faithfulness",
        ),
        "conversation": (
            "relevance",
            "faithfulness",
        ),
        "safety": (),
    }

    @classmethod
    def select(
        cls,
        *,
        evaluation_type: str,
        capabilities: DatasetCapabilities,
        data_policy: DefaultDataPolicy = DefaultDataPolicy.STRICT,
        threshold: float | None = None,
    ) -> DefaultEvaluationPlan:

        normalized_type = evaluation_type.lower()

        candidates = cls.DEFAULT_EVALUATORS.get(
            normalized_type,
            (),
        )

        if data_policy == DefaultDataPolicy.THRESHOLD:
            effective_threshold = threshold if threshold is not None else cls.DEFAULT_THRESHOLD

            if not 0.0 <= effective_threshold <= 1.0:
                raise ValueError("Default evaluation threshold must be between 0.0 and 1.0.")
        else:
            effective_threshold = None

        selected: list[str] = []
        warnings: list[str] = []
        reasons: dict[str, str] = {}

        for evaluator_name in candidates:
            coverage = cls._required_data_coverage(
                evaluator_name,
                capabilities,
            )

            if coverage is None:
                continue

            allowed = cls._is_allowed(
                coverage=coverage,
                data_policy=data_policy,
                threshold=effective_threshold,
            )

            if allowed:
                selected.append(evaluator_name)

                reasons[evaluator_name] = f"Required data coverage is {coverage:.2%}."

            else:
                warnings.append(
                    f"Evaluator '{evaluator_name}' was excluded "
                    f"because required data coverage is "
                    f"{coverage:.2%}."
                )

        return DefaultEvaluationPlan(
            evaluators=tuple(selected),
            data_policy=data_policy,
            threshold=effective_threshold,
            warnings=tuple(warnings),
            reasons=reasons,
        )

    # --------------------------------------------------------------
    # Determine required data coverage
    # --------------------------------------------------------------

    @staticmethod
    def _required_data_coverage(
        evaluator_name: str,
        capabilities: DatasetCapabilities,
    ) -> float | None:

        if evaluator_name in {
            "exact_match",
            "contains",
            "f1",
            "rouge_l",
            "bleu",
        }:
            return capabilities.reference_coverage

        if evaluator_name == "relevance":
            return capabilities.input_coverage

        if evaluator_name == "faithfulness":
            return capabilities.context_coverage

        return None

    # --------------------------------------------------------------
    # Data policy decision
    # --------------------------------------------------------------

    @staticmethod
    def _is_allowed(
        *,
        coverage: float,
        data_policy: DefaultDataPolicy,
        threshold: float | None,
    ) -> bool:

        if data_policy == DefaultDataPolicy.STRICT:
            return coverage == 1.0

        if data_policy == DefaultDataPolicy.PARTIAL:
            return coverage > 0.0

        if data_policy == DefaultDataPolicy.THRESHOLD:
            if threshold is None:
                raise ValueError("Threshold is required for threshold data policy.")

            return coverage >= threshold

        raise ValueError(f"Unsupported default data policy: {data_policy}")


class DefaultEvaluationResolver:
    """
    Resolves the default evaluation plan for a dataset.

    This is the entry point that higher-level services should use.
    """

    @classmethod
    def resolve(
        cls,
        *,
        evaluation_type: str,
        capabilities: DatasetCapabilities,
        data_policy: DefaultDataPolicy = DefaultDataPolicy.STRICT,
        threshold: float | None = None,
    ) -> DefaultEvaluationPlan:

        return DefaultEvaluationPolicy.select(
            evaluation_type=evaluation_type,
            capabilities=capabilities,
            data_policy=data_policy,
            threshold=threshold,
        )
