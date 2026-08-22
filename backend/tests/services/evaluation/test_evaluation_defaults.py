from types import SimpleNamespace

import pytest

from app.services.evaluation.data_policy import DataPolicy
from app.services.evaluation.dataset_capability import (
    DatasetCapabilities,
)
from app.services.evaluation.evaluation_defaults import (
    DefaultEvaluationPolicy,
    DefaultEvaluationResolver,
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


def test_text_default_rules_exist():
    rules = DefaultEvaluationPolicy.get_rules("text")

    names = [rule.evaluator_name for rule in rules]

    assert names == [
        "exact_match",
        "f1",
        "bleu",
        "rouge_l",
    ]


def test_rag_default_rules_exist():
    rules = DefaultEvaluationPolicy.get_rules("rag")

    names = [rule.evaluator_name for rule in rules]

    assert names == [
        "exact_match",
        "f1",
        "relevance",
        "faithfulness",
    ]


def test_unknown_evaluation_type_has_no_defaults():
    assert DefaultEvaluationPolicy.get_rules("unknown") == ()


def test_text_with_full_reference_selects_all_defaults():
    capabilities = make_capabilities(
        reference_coverage=1.0,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "text",
        capabilities,
    )

    assert evaluators == [
        "exact_match",
        "f1",
        "bleu",
        "rouge_l",
    ]


def test_text_without_reference_selects_no_reference_evaluators():
    capabilities = make_capabilities(
        reference_coverage=0.0,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "text",
        capabilities,
    )

    assert evaluators == []


def test_text_partial_reference_is_rejected_by_strict_policy():
    capabilities = make_capabilities(
        reference_coverage=0.80,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "text",
        capabilities,
        policy=DataPolicy.STRICT,
    )

    assert evaluators == []


def test_text_partial_reference_is_allowed_by_partial_policy():
    capabilities = make_capabilities(
        reference_coverage=0.80,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "text",
        capabilities,
        policy=DataPolicy.PARTIAL,
    )

    assert evaluators == [
        "exact_match",
        "f1",
        "bleu",
        "rouge_l",
    ]


def test_text_threshold_policy():
    capabilities = make_capabilities(
        reference_coverage=0.80,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "text",
        capabilities,
        policy=DataPolicy.THRESHOLD,
        threshold=0.80,
    )

    assert evaluators == [
        "exact_match",
        "f1",
        "bleu",
        "rouge_l",
    ]


def test_text_threshold_rejects_below_threshold():
    capabilities = make_capabilities(
        reference_coverage=0.79,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "text",
        capabilities,
        policy=DataPolicy.THRESHOLD,
        threshold=0.80,
    )

    assert evaluators == []


def test_rag_with_full_reference_and_context_selects_all_defaults():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=1.0,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "rag",
        capabilities,
    )

    assert evaluators == [
        "exact_match",
        "f1",
        "relevance",
        "faithfulness",
    ]


def test_rag_with_missing_context_excludes_context_evaluators():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=0.0,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "rag",
        capabilities,
    )

    assert evaluators == [
        "exact_match",
        "f1",
    ]


def test_rag_with_partial_context_strict_policy():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=0.80,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "rag",
        capabilities,
        policy=DataPolicy.STRICT,
    )

    assert evaluators == [
        "exact_match",
        "f1",
    ]


def test_rag_with_partial_context_partial_policy():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=0.80,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "rag",
        capabilities,
        policy=DataPolicy.PARTIAL,
    )

    assert evaluators == [
        "exact_match",
        "f1",
        "relevance",
        "faithfulness",
    ]


def test_rag_threshold_context():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=0.90,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "rag",
        capabilities,
        policy=DataPolicy.THRESHOLD,
        threshold=0.90,
    )

    assert evaluators == [
        "exact_match",
        "f1",
        "relevance",
        "faithfulness",
    ]


def test_rag_threshold_context_below_threshold():
    capabilities = make_capabilities(
        reference_coverage=1.0,
        context_coverage=0.89,
    )

    evaluators = DefaultEvaluationResolver.resolve(
        "rag",
        capabilities,
        policy=DataPolicy.THRESHOLD,
        threshold=0.90,
    )

    assert evaluators == [
        "exact_match",
        "f1",
    ]
