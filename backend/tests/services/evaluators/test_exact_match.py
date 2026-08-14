import pytest

from app.services.evaluators import ExactMatchEvaluator


@pytest.mark.asyncio
async def test_exact_match_returns_one_for_matching_output():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="Paris",
    )

    assert result.metric == "exact_match"
    assert result.score == 1.0
    assert result.feedback == "Output exactly matches the expected answer."


@pytest.mark.asyncio
async def test_exact_match_ignores_surrounding_whitespace():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="  Paris  ",
        actual_output="Paris",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_is_case_sensitive():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="paris",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("expected_output", "actual_output"),
    [
        (None, "Paris"),
        ("Paris", None),
        (None, None),
    ],
)
async def test_exact_match_returns_zero_when_output_is_missing(
    expected_output,
    actual_output,
):
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output=expected_output,
        actual_output=actual_output,
    )

    assert result.score == 0.0
    assert result.feedback == "Expected output or actual output is missing."


def test_exact_match_metadata():
    evaluator = ExactMatchEvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "correctness"

    assert metadata.description == (
        "Checks whether the model output exactly matches "
        "the reference answer after trimming surrounding whitespace."
    )

    assert metadata.requires_reference is True
    assert metadata.requires_context is False
    assert metadata.requires_llm is False

    assert metadata.applicable_to == ("text",)

    assert metadata.tags == (
        "deterministic",
        "reference-based",
        "exact-match",
    )
