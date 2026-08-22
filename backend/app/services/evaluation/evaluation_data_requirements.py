from dataclasses import dataclass
from enum import StrEnum

from app.services.evaluation.data_policy import (
    DataPolicy,
    DataPolicyDecision,
    DataPolicyEvaluator,
)
from app.services.evaluation.dataset_capability import (
    DatasetCapabilities,
)


class DataRequirement(StrEnum):
    """
    Data required by an evaluator.
    """

    REFERENCE = "reference"
    CONTEXT = "context"


@dataclass(frozen=True)
class DataRequirementDecision:
    """
    Result of evaluating one data requirement against
    dataset capabilities.
    """

    requirement: DataRequirement
    decision: DataPolicyDecision


class EvaluationDataRequirementEvaluator:
    """
    Evaluates whether a dataset satisfies a specific evaluator
    data requirement according to a data policy.
    """

    @staticmethod
    def get_coverage(
        capabilities: DatasetCapabilities,
        requirement: DataRequirement,
    ) -> float:
        if requirement == DataRequirement.REFERENCE:
            return capabilities.reference_coverage

        if requirement == DataRequirement.CONTEXT:
            return capabilities.context_coverage

        raise ValueError(f"Unsupported data requirement: {requirement}")

    @classmethod
    def evaluate(
        cls,
        capabilities: DatasetCapabilities,
        requirement: DataRequirement,
        policy: DataPolicy,
        *,
        threshold: float = 1.0,
    ) -> DataRequirementDecision:
        coverage = cls.get_coverage(
            capabilities,
            requirement,
        )

        decision = DataPolicyEvaluator.evaluate(
            policy,
            coverage,
            threshold=threshold,
        )

        return DataRequirementDecision(
            requirement=requirement,
            decision=decision,
        )
