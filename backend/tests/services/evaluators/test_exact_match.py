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
async def test_exact_match_strips_leading_whitespace():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="   Paris",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_strips_trailing_whitespace():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="Paris   ",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_strips_leading_and_trailing_whitespace():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="   Paris   ",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_strips_surrounding_newline_and_tab():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="\n\tParis\t\n",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_normalizes_unicode_nfkc():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="ABC",
        actual_output="ＡＢＣ",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_normalizes_composed_unicode():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Café",
        actual_output="Cafe\u0301",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_preserves_case_sensitivity():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="paris",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
async def test_exact_match_preserves_uppercase_difference():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="PARIS",
        actual_output="Paris",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
async def test_exact_match_preserves_punctuation():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Hello!",
        actual_output="Hello",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
async def test_exact_match_preserves_internal_whitespace():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="hello world",
        actual_output="hello  world",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
async def test_exact_match_does_not_remove_internal_newline():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="hello world",
        actual_output="hello\nworld",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
async def test_exact_match_returns_zero_when_values_are_different():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="London",
    )

    assert result.score == 0.0
    assert result.feedback == "Output does not exactly match the expected answer."


@pytest.mark.asyncio
async def test_exact_match_returns_one_for_both_empty_strings():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="",
        actual_output="",
    )

    assert result.score == 1.0


@pytest.mark.asyncio
async def test_exact_match_returns_zero_when_expected_is_empty():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="",
        actual_output="Paris",
    )

    assert result.score == 0.0


@pytest.mark.asyncio
async def test_exact_match_returns_zero_when_actual_is_empty():
    evaluator = ExactMatchEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="",
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
        "the reference answer after applying normalization."
    )

    assert metadata.required_inputs == (
        "actual_output",
        "expected_output",
    )

    assert metadata.requires_reference is True
    assert metadata.requires_context is False
    assert metadata.requires_llm is False

    assert metadata.applicable_to == ("text", "rag")

    assert metadata.tags == (
        "deterministic",
        "reference-based",
        "exact-match",
        "normalizable",
    )
