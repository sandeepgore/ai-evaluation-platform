import pytest

from app.services.evaluation.data_policy import DataPolicy
from app.services.evaluation.dataset_capability import (
    DatasetCapabilities,
)
from app.services.evaluation.evaluation_data_requirements import (
    DataRequirement,
    EvaluationDataRequirementEvaluator,
)


def make_capabilities(
    *,
    reference_coverage: float = 0.0,
    context_coverage: float = 0.0,
) -> DatasetCapabilities:
    total_cases = 100

    cases_with_reference = int(reference_coverage * total_cases)

    cases_with_context = int(context_coverage * total_cases)

    return DatasetCapabilities(
        total_cases=total_cases,
        cases_with_reference=cases_with_reference,
        cases_without_reference=(total_cases - cases_with_reference),
        cases_with_context=cases_with_context,
        cases_without_context=(total_cases - cases_with_context),
        has_reference=cases_with_reference > 0,
        has_context=cases_with_context > 0,
        all_cases_have_reference=reference_coverage == 1.0,
        all_cases_have_context=context_coverage == 1.0,
        reference_coverage=reference_coverage,
        context_coverage=context_coverage,
    )


def test_reference_requirement_uses_reference_coverage():
    capabilities = make_capabilities(
        reference_coverage=0.75,
        context_coverage=1.0,
    )

    result = EvaluationDataRequirementEvaluator.evaluate(
        capabilities,
        DataRequirement.REFERENCE,
        DataPolicy.THRESHOLD,
        threshold=0.75,
    )

    assert result.requirement == DataRequirement.REFERENCE
    assert result.decision.allowed is True
    assert result.decision.coverage == 0.75


def test_context_requirement_uses_context_coverage():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=0.60,
    )

    result = EvaluationDataRequirementEvaluator.evaluate(
        capabilities,
        DataRequirement.CONTEXT,
        DataPolicy.THRESHOLD,
        threshold=0.80,
    )

    assert result.requirement == DataRequirement.CONTEXT
    assert result.decision.allowed is False
    assert result.decision.coverage == 0.60


def test_strict_reference_requirement_requires_full_coverage():
    capabilities = make_capabilities(
        reference_coverage=0.99,
    )

    result = EvaluationDataRequirementEvaluator.evaluate(
        capabilities,
        DataRequirement.REFERENCE,
        DataPolicy.STRICT,
    )

    assert result.decision.allowed is False
    assert result.decision.required_coverage == 1.0


def test_strict_context_requirement_allows_full_coverage():
    capabilities = make_capabilities(
        context_coverage=1.0,
    )

    result = EvaluationDataRequirementEvaluator.evaluate(
        capabilities,
        DataRequirement.CONTEXT,
        DataPolicy.STRICT,
    )

    assert result.decision.allowed is True
    assert result.decision.coverage == 1.0


def test_partial_reference_requirement_allows_non_zero_coverage():
    capabilities = make_capabilities(
        reference_coverage=0.10,
    )

    result = EvaluationDataRequirementEvaluator.evaluate(
        capabilities,
        DataRequirement.REFERENCE,
        DataPolicy.PARTIAL,
    )

    assert result.decision.allowed is True


def test_partial_context_requirement_rejects_zero_coverage():
    capabilities = make_capabilities(
        context_coverage=0.0,
    )

    result = EvaluationDataRequirementEvaluator.evaluate(
        capabilities,
        DataRequirement.CONTEXT,
        DataPolicy.PARTIAL,
    )

    assert result.decision.allowed is False


@pytest.mark.parametrize(
    (
        "requirement",
        "reference_coverage",
        "context_coverage",
        "expected_coverage",
    ),
    [
        (
            DataRequirement.REFERENCE,
            0.70,
            0.30,
            0.70,
        ),
        (
            DataRequirement.CONTEXT,
            0.70,
            0.30,
            0.30,
        ),
    ],
)
def test_get_coverage_maps_requirement_correctly(
    requirement,
    reference_coverage,
    context_coverage,
    expected_coverage,
):
    capabilities = make_capabilities(
        reference_coverage=reference_coverage,
        context_coverage=context_coverage,
    )

    coverage = EvaluationDataRequirementEvaluator.get_coverage(
        capabilities,
        requirement,
    )

    assert coverage == expected_coverage
