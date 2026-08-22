from dataclasses import dataclass

from app.services.evaluation.data_policy import DataPolicy
from app.services.evaluation.dataset_capability import DatasetCapabilities
from app.services.evaluation.evaluation_data_requirements import (
    DataRequirement,
    EvaluationDataRequirementEvaluator,
)


@dataclass(frozen=True)
class DefaultEvaluatorRule:
    """
    Defines the data requirements for an evaluator
    that may be selected by default.
    """

    evaluator_name: str
    requirements: tuple[DataRequirement, ...] = ()


@dataclass(frozen=True)
class DefaultEvaluatorDecision:
    """
    Result for one default evaluator.
    """

    evaluator_name: str
    selected: bool
    reason: str


class DefaultEvaluationPolicy:
    """
    Defines the platform's default evaluator selection policy.

    This class contains policy only. It does not access the database,
    execute evaluators, or execute the evaluation engine.
    """

    RULES = {
        "text": (
            DefaultEvaluatorRule(
                evaluator_name="exact_match",
                requirements=(DataRequirement.REFERENCE,),
            ),
            DefaultEvaluatorRule(
                evaluator_name="f1",
                requirements=(DataRequirement.REFERENCE,),
            ),
            DefaultEvaluatorRule(
                evaluator_name="bleu",
                requirements=(DataRequirement.REFERENCE,),
            ),
            DefaultEvaluatorRule(
                evaluator_name="rouge_l",
                requirements=(DataRequirement.REFERENCE,),
            ),
        ),
        "rag": (
            DefaultEvaluatorRule(
                evaluator_name="exact_match",
                requirements=(DataRequirement.REFERENCE,),
            ),
            DefaultEvaluatorRule(
                evaluator_name="f1",
                requirements=(DataRequirement.REFERENCE,),
            ),
            DefaultEvaluatorRule(
                evaluator_name="relevance",
                requirements=(DataRequirement.CONTEXT,),
            ),
            DefaultEvaluatorRule(
                evaluator_name="faithfulness",
                requirements=(DataRequirement.CONTEXT,),
            ),
        ),
    }

    @classmethod
    def get_rules(
        cls,
        evaluation_type: str,
    ) -> tuple[DefaultEvaluatorRule, ...]:
        return cls.RULES.get(
            evaluation_type.lower(),
            (),
        )


class DefaultEvaluationResolver:
    """
    Resolves default evaluators using:

        evaluation type
            +
        dataset capabilities
            +
        data policy
            ↓
        selected evaluators

    No database access occurs here.
    """

    @classmethod
    def resolve(
        cls,
        evaluation_type: str,
        capabilities: DatasetCapabilities,
        *,
        policy: DataPolicy = DataPolicy.STRICT,
        threshold: float = 1.0,
    ) -> list[str]:
        decisions = cls.resolve_with_decisions(
            evaluation_type,
            capabilities,
            policy=policy,
            threshold=threshold,
        )

        return [decision.evaluator_name for decision in decisions if decision.selected]

    @classmethod
    def resolve_with_decisions(
        cls,
        evaluation_type: str,
        capabilities: DatasetCapabilities,
        *,
        policy: DataPolicy = DataPolicy.STRICT,
        threshold: float = 1.0,
    ) -> list[DefaultEvaluatorDecision]:
        rules = DefaultEvaluationPolicy.get_rules(evaluation_type)

        decisions: list[DefaultEvaluatorDecision] = []

        for rule in rules:
            failed_requirements: list[str] = []

            for requirement in rule.requirements:
                result = EvaluationDataRequirementEvaluator.evaluate(
                    capabilities,
                    requirement,
                    policy,
                    threshold=threshold,
                )

                if not result.decision.allowed:
                    failed_requirements.append(f"{requirement.value}: {result.decision.reason}")

            if failed_requirements:
                decisions.append(
                    DefaultEvaluatorDecision(
                        evaluator_name=rule.evaluator_name,
                        selected=False,
                        reason="; ".join(failed_requirements),
                    )
                )
            else:
                decisions.append(
                    DefaultEvaluatorDecision(
                        evaluator_name=rule.evaluator_name,
                        selected=True,
                        reason="All required data is available.",
                    )
                )

        return decisions
