from types import SimpleNamespace

from app.services.evaluation.dataset_capability import (
    DatasetCapabilityAnalyzer,
)


def make_case(
    *,
    has_reference=False,
    has_context=False,
):
    return SimpleNamespace(
        has_reference=has_reference,
        has_context=has_context,
    )


def test_empty_dataset_has_no_capabilities():
    capabilities = DatasetCapabilityAnalyzer.analyze([])

    assert capabilities.total_cases == 0

    assert capabilities.has_reference is False
    assert capabilities.has_context is False

    assert capabilities.all_cases_have_reference is False
    assert capabilities.all_cases_have_context is False

    assert capabilities.reference_coverage == 0.0
    assert capabilities.context_coverage == 0.0


def test_reference_is_detected():
    cases = [
        make_case(has_reference=True),
        make_case(has_reference=True),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.total_cases == 2

    assert capabilities.cases_with_reference == 2
    assert capabilities.cases_without_reference == 0

    assert capabilities.has_reference is True
    assert capabilities.all_cases_have_reference is True

    assert capabilities.reference_coverage == 1.0


def test_missing_reference_is_not_considered_available():
    cases = [
        make_case(has_reference=False),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_reference is False
    assert capabilities.all_cases_have_reference is False
    assert capabilities.cases_with_reference == 0
    assert capabilities.cases_without_reference == 1
    assert capabilities.reference_coverage == 0.0


def test_partial_reference_coverage_is_detected():
    cases = [
        make_case(has_reference=True),
        make_case(has_reference=False),
        make_case(has_reference=True),
        make_case(has_reference=False),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.total_cases == 4

    assert capabilities.cases_with_reference == 2
    assert capabilities.cases_without_reference == 2

    assert capabilities.has_reference is True
    assert capabilities.all_cases_have_reference is False

    assert capabilities.reference_coverage == 0.5


def test_context_is_detected():
    cases = [
        make_case(has_context=True),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is True
    assert capabilities.all_cases_have_context is True

    assert capabilities.cases_with_context == 1
    assert capabilities.cases_without_context == 0
    assert capabilities.context_coverage == 1.0


def test_no_context_is_not_considered_available():
    cases = [
        make_case(has_context=False),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is False
    assert capabilities.all_cases_have_context is False

    assert capabilities.cases_with_context == 0
    assert capabilities.cases_without_context == 1
    assert capabilities.context_coverage == 0.0


def test_partial_context_coverage_is_detected():
    cases = [
        make_case(has_context=True),
        make_case(has_context=False),
        make_case(has_context=True),
        make_case(has_context=False),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.total_cases == 4

    assert capabilities.cases_with_context == 2
    assert capabilities.cases_without_context == 2

    assert capabilities.has_context is True
    assert capabilities.all_cases_have_context is False

    assert capabilities.context_coverage == 0.5


def test_reference_and_context_can_exist_together():
    cases = [
        make_case(
            has_reference=True,
            has_context=True,
        ),
        make_case(
            has_reference=True,
            has_context=True,
        ),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_reference is True
    assert capabilities.has_context is True

    assert capabilities.all_cases_have_reference is True
    assert capabilities.all_cases_have_context is True

    assert capabilities.reference_coverage == 1.0
    assert capabilities.context_coverage == 1.0


def test_reference_and_context_can_be_partial_independently():
    cases = [
        make_case(
            has_reference=True,
            has_context=True,
        ),
        make_case(
            has_reference=True,
            has_context=False,
        ),
        make_case(
            has_reference=False,
            has_context=True,
        ),
        make_case(
            has_reference=False,
            has_context=False,
        ),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.total_cases == 4

    assert capabilities.cases_with_reference == 2
    assert capabilities.cases_without_reference == 2
    assert capabilities.reference_coverage == 0.5

    assert capabilities.cases_with_context == 2
    assert capabilities.cases_without_context == 2
    assert capabilities.context_coverage == 0.5

    assert capabilities.has_reference is True
    assert capabilities.has_context is True

    assert capabilities.all_cases_have_reference is False
    assert capabilities.all_cases_have_context is False
