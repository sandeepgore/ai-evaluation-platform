import pytest

from app.services.evaluators.applicability import (
    EvaluationCapabilities,
    EvaluatorApplicabilityService,
)
from app.services.evaluators.registry import create_default_registry


@pytest.fixture
def service() -> EvaluatorApplicabilityService:
    return EvaluatorApplicabilityService(create_default_registry())


def test_reference_evaluator_is_applicable_when_reference_exists(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=True,
        has_context=False,
        llm_available=False,
    )

    evaluators = service.validate(
        ["exact_match"],
        capabilities,
    )

    assert len(evaluators) == 1
    assert evaluators[0].name == "exact_match"


def test_reference_evaluator_is_rejected_without_reference(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=False,
        has_context=False,
        llm_available=False,
    )

    with pytest.raises(ValueError, match="requires a reference"):
        service.validate(
            ["exact_match"],
            capabilities,
        )


def test_context_evaluator_is_rejected_without_context(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=False,
        has_context=False,
        llm_available=False,
    )

    with pytest.raises(ValueError, match="requires evaluation context"):
        service.validate(
            ["faithfulness"],
            capabilities,
        )


def test_context_evaluator_is_allowed_with_context(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=False,
        has_context=True,
        llm_available=False,
    )

    evaluators = service.validate(
        ["faithfulness"],
        capabilities,
    )

    assert len(evaluators) == 1
    assert evaluators[0].name == "faithfulness"


def test_unknown_evaluator_is_rejected(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
    )

    with pytest.raises(ValueError, match="Unknown evaluator"):
        service.validate(
            ["does_not_exist"],
            capabilities,
        )


def test_duplicate_alias_is_rejected(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=True,
    )

    with pytest.raises(ValueError, match="selected more than once"):
        service.validate(
            ["rouge_l", "rouge"],
            capabilities,
        )


def test_multiple_evaluators_are_validated(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=True,
        has_context=False,
    )

    evaluators = service.validate(
        [
            "exact_match",
            "f1",
            "bleu",
            "rouge_l",
        ],
        capabilities,
    )

    assert [evaluator.name for evaluator in evaluators] == [
        "exact_match",
        "f1",
        "bleu",
        "rouge_l",
    ]


def test_configuration_supports_string_evaluators(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=True,
    )

    evaluators = service.validate_configuration(
        {
            "evaluators": [
                "exact_match",
                "f1",
            ]
        },
        capabilities,
    )

    assert [evaluator.name for evaluator in evaluators] == [
        "exact_match",
        "f1",
    ]


def test_configuration_supports_object_evaluators(service):
    capabilities = EvaluationCapabilities(
        evaluation_type="text",
        has_reference=True,
    )

    evaluators = service.validate_configuration(
        {
            "evaluators": [
                {
                    "name": "exact_match",
                    "weight": 0.5,
                },
                {
                    "name": "f1",
                    "weight": 0.5,
                },
            ]
        },
        capabilities,
    )

    assert [evaluator.name for evaluator in evaluators] == [
        "exact_match",
        "f1",
    ]
