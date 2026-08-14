import math

import pytest

from app.services.evaluators import BLEUEvaluator


@pytest.mark.asyncio
async def test_bleu_returns_one_for_identical_output():
    evaluator = BLEUEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France",
        actual_output="Paris is the capital of France",
    )

    assert result.metric == "bleu"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["precisions"]["1-gram"] == pytest.approx(1.0)
    assert result.metadata["precisions"]["2-gram"] == pytest.approx(1.0)
    assert result.metadata["precisions"]["3-gram"] == pytest.approx(1.0)
    assert result.metadata["precisions"]["4-gram"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_bleu_returns_zero_when_there_is_no_overlap():
    evaluator = BLEUEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris France",
        actual_output="Tokyo Japan",
    )

    assert result.score == 0.0
    assert result.metadata["precisions"]["1-gram"] == 0.0


@pytest.mark.asyncio
async def test_bleu_handles_repeated_ngrams_with_clipping():
    evaluator = BLEUEvaluator()

    result = await evaluator.evaluate(
        expected_output="RAG RAG system",
        actual_output="RAG RAG RAG system",
    )

    assert result.metadata["matched_counts"]["1-gram"] == 3
    assert result.metadata["total_counts"]["1-gram"] == 4
    assert result.score == 0.0


@pytest.mark.asyncio
async def test_bleu_applies_brevity_penalty():
    evaluator = BLEUEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France",
        actual_output="Paris is the capital",
    )

    expected_brevity_penalty = math.exp(1 - 6 / 4)

    assert result.metadata["brevity_penalty"] < 1.0
    assert result.metadata["brevity_penalty"] == pytest.approx(expected_brevity_penalty)

    assert result.metadata["reference_length"] == 6
    assert result.metadata["actual_length"] == 4

    assert result.score == pytest.approx(expected_brevity_penalty)


@pytest.mark.asyncio
async def test_bleu_returns_zero_for_empty_output():
    evaluator = BLEUEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris",
        actual_output="   ",
    )

    assert result.score == 0.0
    assert result.feedback == ("Expected output or actual output is empty.")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("expected_output", "actual_output"),
    [
        (None, "Paris"),
        ("Paris", None),
        (None, None),
    ],
)
async def test_bleu_returns_zero_when_output_is_missing(
    expected_output,
    actual_output,
):
    evaluator = BLEUEvaluator()

    result = await evaluator.evaluate(
        expected_output=expected_output,
        actual_output=actual_output,
    )

    assert result.score == 0.0
    assert result.feedback == ("Expected output or actual output is missing.")


def test_bleu_metadata():
    evaluator = BLEUEvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "similarity"

    assert metadata.description == (
        "Measures n-gram overlap between the model output and "
        "the reference answer using deterministic BLEU-4 scoring."
    )

    assert metadata.requires_reference is True
    assert metadata.requires_context is False
    assert metadata.requires_llm is False
    assert metadata.applicable_to == ("text",)

    assert metadata.tags == (
        "deterministic",
        "reference-based",
        "n-gram",
        "bleu",
    )
