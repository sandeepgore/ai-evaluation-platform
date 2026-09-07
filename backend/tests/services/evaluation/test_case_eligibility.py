from types import SimpleNamespace

from app.services.evaluation.case_eligibility import (
    CaseEligibilityEvaluator,
)
from app.services.evaluators.base import EvaluatorMetadata


def make_case(
    *,
    has_reference=False,
    has_context=False,
):
    return SimpleNamespace(
        has_reference=has_reference,
        has_context=has_context,
    )


def test_case_is_eligible_when_no_requirements_are_declared():
    case = make_case()

    metadata = EvaluatorMetadata()

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is True
    assert decision.missing_requirements == ()
    assert decision.reason == "Case contains all required evaluator inputs."


def test_reference_required_and_present():
    case = make_case(
        has_reference=True,
    )

    metadata = EvaluatorMetadata(
        requires_reference=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is True
    assert decision.missing_requirements == ()


def test_reference_required_and_missing():
    case = make_case(
        has_reference=False,
    )

    metadata = EvaluatorMetadata(
        requires_reference=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is False
    assert decision.missing_requirements == ("reference",)
    assert decision.reason == "Missing required input(s): reference."


def test_context_required_and_present():
    case = make_case(
        has_context=True,
    )

    metadata = EvaluatorMetadata(
        requires_context=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is True
    assert decision.missing_requirements == ()


def test_context_required_and_missing():
    case = make_case(
        has_context=False,
    )

    metadata = EvaluatorMetadata(
        requires_context=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is False
    assert decision.missing_requirements == ("context",)
    assert decision.reason == "Missing required input(s): context."


def test_both_requirements_present():
    case = make_case(
        has_reference=True,
        has_context=True,
    )

    metadata = EvaluatorMetadata(
        requires_reference=True,
        requires_context=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is True
    assert decision.missing_requirements == ()


def test_both_requirements_missing():
    case = make_case(
        has_reference=False,
        has_context=False,
    )

    metadata = EvaluatorMetadata(
        requires_reference=True,
        requires_context=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is False
    assert decision.missing_requirements == (
        "reference",
        "context",
    )
    assert decision.reason == "Missing required input(s): reference, context."


def test_only_missing_requirement_is_reported():
    case = make_case(
        has_reference=True,
        has_context=False,
    )

    metadata = EvaluatorMetadata(
        requires_reference=True,
        requires_context=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is False
    assert decision.missing_requirements == ("context",)


def test_only_reference_missing_is_reported():
    case = make_case(
        has_reference=False,
        has_context=True,
    )

    metadata = EvaluatorMetadata(
        requires_reference=True,
        requires_context=True,
    )

    decision = CaseEligibilityEvaluator.evaluate(
        case=case,
        metadata=metadata,
    )

    assert decision.eligible is False
    assert decision.missing_requirements == ("reference",)


def test_reference_and_context_are_independent():
    cases = [
        make_case(
            has_reference=True,
            has_context=False,
        ),
        make_case(
            has_reference=False,
            has_context=True,
        ),
    ]

    reference_metadata = EvaluatorMetadata(
        requires_reference=True,
    )

    context_metadata = EvaluatorMetadata(
        requires_context=True,
    )

    reference_decision = CaseEligibilityEvaluator.evaluate(
        case=cases[0],
        metadata=reference_metadata,
    )

    context_decision = CaseEligibilityEvaluator.evaluate(
        case=cases[1],
        metadata=context_metadata,
    )

    assert reference_decision.eligible is True
    assert context_decision.eligible is True
