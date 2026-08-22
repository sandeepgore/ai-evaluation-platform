from dataclasses import dataclass
from enum import StrEnum


class DataPolicy(StrEnum):
    """
    Defines how missing evaluation data should be handled.
    """

    STRICT = "strict"
    PARTIAL = "partial"
    THRESHOLD = "threshold"


@dataclass(frozen=True)
class DataPolicyDecision:
    """
    Result of applying a data policy to a capability requirement.
    """

    allowed: bool
    coverage: float
    required_coverage: float
    reason: str


class DataPolicyEvaluator:
    """
    Applies data availability policies to dataset capabilities.

    This class intentionally has no dependency on:
        - SQLAlchemy
        - FastAPI
        - DatasetCase
        - EvaluatorRegistry
        - EvaluationEngine

    It only evaluates coverage values.
    """

    @staticmethod
    def evaluate(
        policy: DataPolicy,
        coverage: float,
        *,
        threshold: float = 1.0,
    ) -> DataPolicyDecision:
        """
        Evaluate whether a capability is available according to a policy.

        STRICT:
            Requires 100% coverage.

        PARTIAL:
            Allows any non-zero coverage.

        THRESHOLD:
            Requires coverage >= configured threshold.
        """

        if not 0.0 <= coverage <= 1.0:
            raise ValueError("Coverage must be between 0.0 and 1.0.")

        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0.")

        if policy == DataPolicy.STRICT:
            required_coverage = 1.0
            allowed = coverage == 1.0

            reason = (
                "All cases contain the required data."
                if allowed
                else "Strict policy requires 100% data coverage."
            )

        elif policy == DataPolicy.PARTIAL:
            required_coverage = 0.0
            allowed = coverage > 0.0

            reason = (
                "At least one case contains the required data."
                if allowed
                else "Partial policy requires at least one case with the required data."
            )

        elif policy == DataPolicy.THRESHOLD:
            required_coverage = threshold
            allowed = coverage >= threshold

            reason = (
                f"Coverage meets the required threshold of {threshold:.2f}."
                if allowed
                else f"Coverage is below the required threshold of {threshold:.2f}."
            )

        else:
            raise ValueError(f"Unsupported data policy: {policy}")

        return DataPolicyDecision(
            allowed=allowed,
            coverage=coverage,
            required_coverage=required_coverage,
            reason=reason,
        )
