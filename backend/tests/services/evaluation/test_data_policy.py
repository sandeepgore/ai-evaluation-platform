import pytest

from app.services.evaluation.data_policy import (
    DataPolicy,
    DataPolicyEvaluator,
)


def test_strict_allows_full_coverage():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.STRICT,
        coverage=1.0,
    )

    assert decision.allowed is True
    assert decision.coverage == 1.0
    assert decision.required_coverage == 1.0


def test_strict_rejects_partial_coverage():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.STRICT,
        coverage=0.75,
    )

    assert decision.allowed is False
    assert decision.coverage == 0.75
    assert decision.required_coverage == 1.0


def test_strict_rejects_zero_coverage():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.STRICT,
        coverage=0.0,
    )

    assert decision.allowed is False


def test_partial_allows_any_non_zero_coverage():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.PARTIAL,
        coverage=0.01,
    )

    assert decision.allowed is True
    assert decision.required_coverage == 0.0


def test_partial_allows_full_coverage():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.PARTIAL,
        coverage=1.0,
    )

    assert decision.allowed is True


def test_partial_rejects_zero_coverage():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.PARTIAL,
        coverage=0.0,
    )

    assert decision.allowed is False


def test_threshold_allows_coverage_at_threshold():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.THRESHOLD,
        coverage=0.80,
        threshold=0.80,
    )

    assert decision.allowed is True
    assert decision.required_coverage == 0.80


def test_threshold_allows_coverage_above_threshold():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.THRESHOLD,
        coverage=0.95,
        threshold=0.80,
    )

    assert decision.allowed is True


def test_threshold_rejects_coverage_below_threshold():
    decision = DataPolicyEvaluator.evaluate(
        DataPolicy.THRESHOLD,
        coverage=0.79,
        threshold=0.80,
    )

    assert decision.allowed is False
    assert decision.required_coverage == 0.80


@pytest.mark.parametrize(
    "coverage",
    [-0.01, 1.01],
)
def test_invalid_coverage_is_rejected(coverage):
    with pytest.raises(
        ValueError,
        match="Coverage must be between 0.0 and 1.0",
    ):
        DataPolicyEvaluator.evaluate(
            DataPolicy.STRICT,
            coverage=coverage,
        )


@pytest.mark.parametrize(
    "threshold",
    [-0.01, 1.01],
)
def test_invalid_threshold_is_rejected(threshold):
    with pytest.raises(
        ValueError,
        match="Threshold must be between 0.0 and 1.0",
    ):
        DataPolicyEvaluator.evaluate(
            DataPolicy.THRESHOLD,
            coverage=0.80,
            threshold=threshold,
        )
