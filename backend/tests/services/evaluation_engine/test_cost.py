import pytest

from app.services.evaluation_engine.cost import EvaluationCostService


def test_calculates_input_output_and_total_cost():
    result = EvaluationCostService.calculate(
        input_tokens=1_000_000,
        output_tokens=500_000,
        input_price_per_million=5.0,
        output_price_per_million=15.0,
    )

    assert result["input_cost"] == pytest.approx(5.0)
    assert result["output_cost"] == pytest.approx(7.5)
    assert result["total_cost"] == pytest.approx(12.5)
    assert result["currency"] == "USD"


def test_returns_zero_cost_when_pricing_is_zero():
    result = EvaluationCostService.calculate(
        input_tokens=954,
        output_tokens=1039,
    )

    assert result["input_cost"] == pytest.approx(0.0)
    assert result["output_cost"] == pytest.approx(0.0)
    assert result["total_cost"] == pytest.approx(0.0)
    assert result["currency"] == "USD"


def test_calculates_cost_for_small_token_usage():
    result = EvaluationCostService.calculate(
        input_tokens=954,
        output_tokens=1039,
        input_price_per_million=5.0,
        output_price_per_million=15.0,
    )

    assert result["input_cost"] == pytest.approx(0.00477)
    assert result["output_cost"] == pytest.approx(0.015585)
    assert result["total_cost"] == pytest.approx(0.020355)
    assert result["currency"] == "USD"


def test_supports_custom_currency():
    result = EvaluationCostService.calculate(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        input_price_per_million=1.0,
        output_price_per_million=2.0,
        currency="EUR",
    )

    assert result["input_cost"] == pytest.approx(1.0)
    assert result["output_cost"] == pytest.approx(2.0)
    assert result["total_cost"] == pytest.approx(3.0)
    assert result["currency"] == "EUR"


def test_handles_zero_tokens():
    result = EvaluationCostService.calculate(
        input_tokens=0,
        output_tokens=0,
        input_price_per_million=5.0,
        output_price_per_million=15.0,
    )

    assert result["input_cost"] == pytest.approx(0.0)
    assert result["output_cost"] == pytest.approx(0.0)
    assert result["total_cost"] == pytest.approx(0.0)
