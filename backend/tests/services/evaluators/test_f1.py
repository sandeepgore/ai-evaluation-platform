import pytest

from app.services.evaluators import F1Evaluator


@pytest.mark.asyncio
async def test_f1_returns_one_for_identical_output():
    evaluator = F1Evaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France",
        actual_output="Paris is the capital of France",
    )

    assert result.metric == "f1"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["precision"] == pytest.approx(1.0)
    assert result.metadata["recall"] == pytest.approx(1.0)
    assert result.metadata["overlap"] == 6


@pytest.mark.asyncio
async def test_f1_calculates_partial_token_overlap():
    evaluator = F1Evaluator()

    result = await evaluator.evaluate(
        expected_output="RAG combines retrieval and generation.",
        actual_output="RAG combines information.",
    )

    assert result.score == pytest.approx(0.5)
    assert result.metadata["precision"] == pytest.approx(2 / 3)
    assert result.metadata["recall"] == pytest.approx(2 / 5)
    assert result.metadata["overlap"] == 2
    assert result.metadata["expected_tokens"] == 5
    assert result.metadata["actual_tokens"] == 3


@pytest.mark.asyncio
async def test_f1_returns_zero_when_there_is_no_overlap():
    evaluator = F1Evaluator()

    result = await evaluator.evaluate(
        expected_output="Paris France",
        actual_output="Tokyo Japan",
    )

    assert result.score == 0.0
    assert result.metadata["precision"] == 0.0
    assert result.metadata["recall"] == 0.0
    assert result.feedback == (
        "No token overlap between expected and actual output."
    )


@pytest.mark.asyncio
async def test_f1_handles_repeated_tokens():
    evaluator = F1Evaluator()

    result = await evaluator.evaluate(
        expected_output="RAG RAG system",
        actual_output="RAG system",
    )

    assert result.metadata["overlap"] == 2
    assert result.score == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_f1_returns_zero_for_empty_output():
    evaluator = F1Evaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="   ",
    )

    assert result.score == 0.0
    assert result.feedback == (
        "Expected output or actual output is empty."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("expected_output", "actual_output"),
    [
        (None, "Paris"),
        ("Paris", None),
        (None, None),
    ],
)
async def test_f1_returns_zero_when_output_is_missing(
    expected_output,
    actual_output,
):
    evaluator = F1Evaluator()

    result = await evaluator.evaluate(
        expected_output=expected_output,
        actual_output=actual_output,
    )

    assert result.score == 0.0
    assert result.feedback == "Expected output or actual output is missing."