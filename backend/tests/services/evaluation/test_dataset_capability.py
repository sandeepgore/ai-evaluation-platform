from types import SimpleNamespace

import pytest

from app.services.evaluation.dataset_capability import (
    DatasetCapabilityAnalyzer,
)


def make_case(
    *,
    expected_output=None,
    case_metadata=None,
):
    return SimpleNamespace(
        expected_output=expected_output,
        case_metadata=case_metadata,
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
        make_case(expected_output="Paris"),
        make_case(expected_output="London"),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.total_cases == 2

    assert capabilities.cases_with_reference == 2
    assert capabilities.cases_without_reference == 0

    assert capabilities.has_reference is True
    assert capabilities.all_cases_have_reference is True

    assert capabilities.reference_coverage == 1.0


@pytest.mark.parametrize(
    "expected_output",
    [
        None,
        "",
        "   ",
    ],
)
def test_empty_reference_is_not_considered_available(expected_output):
    cases = [
        make_case(expected_output=expected_output),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_reference is False
    assert capabilities.all_cases_have_reference is False
    assert capabilities.cases_with_reference == 0
    assert capabilities.cases_without_reference == 1
    assert capabilities.reference_coverage == 0.0


def test_partial_reference_coverage_is_detected():
    cases = [
        make_case(expected_output="Paris"),
        make_case(expected_output=None),
        make_case(expected_output="London"),
        make_case(expected_output=""),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.total_cases == 4

    assert capabilities.cases_with_reference == 2
    assert capabilities.cases_without_reference == 2

    assert capabilities.has_reference is True
    assert capabilities.all_cases_have_reference is False

    assert capabilities.reference_coverage == 0.5


def test_context_string_is_detected():
    cases = [
        make_case(
            case_metadata={
                "context": "Paris is the capital of France.",
            }
        )
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is True
    assert capabilities.all_cases_have_context is True

    assert capabilities.cases_with_context == 1
    assert capabilities.context_coverage == 1.0


def test_retrieved_context_string_is_detected():
    cases = [
        make_case(
            case_metadata={
                "retrieved_context": "Paris is the capital of France.",
            }
        )
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is True


def test_reference_context_string_is_detected():
    cases = [
        make_case(
            case_metadata={
                "reference_context": "Paris is the capital of France.",
            }
        )
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is True


def test_context_list_is_detected():
    cases = [
        make_case(
            case_metadata={
                "context": [
                    "Paris is the capital of France.",
                    "France is in Europe.",
                ],
            }
        )
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is True
    assert capabilities.all_cases_have_context is True


def test_empty_context_is_not_detected():
    cases = [
        make_case(
            case_metadata={
                "context": "",
            }
        ),
        make_case(
            case_metadata={
                "context": [],
            }
        ),
        make_case(
            case_metadata={
                "context": ["", "   "],
            }
        ),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_context is False
    assert capabilities.cases_with_context == 0
    assert capabilities.context_coverage == 0.0


def test_missing_metadata_is_not_context():
    cases = [
        make_case(expected_output="Paris"),
        make_case(expected_output="London", case_metadata=None),
        make_case(expected_output="Rome", case_metadata={}),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_reference is True
    assert capabilities.has_context is False

    assert capabilities.cases_with_context == 0
    assert capabilities.cases_without_context == 3


def test_partial_context_coverage_is_detected():
    cases = [
        make_case(
            case_metadata={
                "context": "Paris is the capital of France.",
            }
        ),
        make_case(
            case_metadata=None,
        ),
        make_case(
            case_metadata={
                "retrieved_context": [
                    "London is the capital of England.",
                ],
            }
        ),
        make_case(
            case_metadata={
                "context": "",
            }
        ),
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
            expected_output="Paris",
            case_metadata={
                "context": "Paris is the capital of France.",
            },
        ),
        make_case(
            expected_output="London",
            case_metadata={
                "context": "London is the capital of England.",
            },
        ),
    ]

    capabilities = DatasetCapabilityAnalyzer.analyze(cases)

    assert capabilities.has_reference is True
    assert capabilities.has_context is True

    assert capabilities.all_cases_have_reference is True
    assert capabilities.all_cases_have_context is True

    assert capabilities.reference_coverage == 1.0
    assert capabilities.context_coverage == 1.0
