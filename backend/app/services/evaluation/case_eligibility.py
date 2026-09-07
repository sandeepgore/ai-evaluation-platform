from dataclasses import dataclass
from typing import Any

from app.services.evaluators.base import EvaluatorMetadata


@dataclass(frozen=True)
class CaseEligibilityDecision:
    """
    Result of evaluating whether a dataset case can be evaluated
    by a specific evaluator.
    """

    eligible: bool
    missing_requirements: tuple[str, ...]
    reason: str


class CaseEligibilityEvaluator:
    """
    Pure business-logic evaluator for case-level eligibility.

    Capability flags are derived during dataset ingestion and persisted
    on DatasetCase. This evaluator consumes those persisted flags and
    does not recalculate capabilities from raw case data.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        case: Any,
        metadata: EvaluatorMetadata,
    ) -> CaseEligibilityDecision:
        missing_requirements: list[str] = []

        if metadata.requires_reference and not case.has_reference:
            missing_requirements.append("reference")

        if metadata.requires_context and not case.has_context:
            missing_requirements.append("context")

        if missing_requirements:
            missing = ", ".join(missing_requirements)

            return CaseEligibilityDecision(
                eligible=False,
                missing_requirements=tuple(missing_requirements),
                reason=f"Missing required input(s): {missing}.",
            )

        return CaseEligibilityDecision(
            eligible=True,
            missing_requirements=(),
            reason="Case contains all required evaluator inputs.",
        )
