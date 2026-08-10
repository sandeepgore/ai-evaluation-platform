import pytest

from app.services.evaluators import ContainsEvaluator


@pytest.mark.asyncio
async def test_contains_returns_one_when_expected_is_present():
    evaluator = ContainsEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="The capital of France is Paris.",
    )

    assert result.metric == "contains"
    assert result.score == 1.0
    assert result.feedback == (
        "Expected output is contained in the actual output."
    )


@pytest.mark.asyncio
async def test_contains_is_case_insensitive():
    evaluator = ContainsEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="The capital is PARIS.",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_contains_ignores_surrounding_whitespace():
    evaluator = ContainsEvaluator()

    result = await evaluator.evaluate(
        expected_output="  Paris  ",
        actual_output="Paris",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_contains_returns_zero_when_expected_is_missing():
    evaluator = ContainsEvaluator()

    result = await evaluator.evaluate(
        expected_output="London",
        actual_output="The capital of France is Paris.",
    )

    assert result.score == 0.0
    assert result.feedback == (
        "Expected output is not contained in the actual output."
    )


@pytest.mark.asyncio
async def test_contains_returns_zero_for_empty_expected_output():
    evaluator = ContainsEvaluator()

    result = await evaluator.evaluate(
        expected_output="   ",
        actual_output="Paris",
    )

    assert result.score == 0.0
    assert result.feedback == "Expected output is empty."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("expected_output", "actual_output"),
    [
        (None, "Paris"),
        ("Paris", None),
        (None, None),
    ],
)
async def test_contains_returns_zero_when_output_is_missing(
    expected_output,
    actual_output,
):
    evaluator = ContainsEvaluator()

    result = await evaluator.evaluate(
        expected_output=expected_output,
        actual_output=actual_output,
    )

    assert result.score == 0.0
    assert result.feedback == "Expected output or actual output is missing."