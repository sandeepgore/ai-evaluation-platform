import pytest

from app.services.evaluators import FaithfulnessEvaluator


@pytest.mark.asyncio
async def test_faithfulness_returns_one_when_output_is_fully_supported():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is the capital of France.",
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.metric == "faithfulness"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["supported_tokens"] > 0


@pytest.mark.asyncio
async def test_faithfulness_calculates_partial_support():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is the capital of France and Germany.",
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert 0.0 < result.score < 1.0
    assert result.metadata["supported_tokens"] > 0
    assert result.metadata["unsupported_tokens"] > 0


@pytest.mark.asyncio
async def test_faithfulness_returns_zero_when_output_is_not_supported():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Tokyo is located in Japan.",
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == 0.0
    assert result.metadata["supported_tokens"] == 0


@pytest.mark.asyncio
async def test_faithfulness_ignores_case_and_punctuation():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="PARIS is the capital of FRANCE!",
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_faithfulness_returns_zero_for_empty_output():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="   ",
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == 0.0
    assert result.feedback == "Context or actual output is empty."


@pytest.mark.asyncio
async def test_faithfulness_returns_zero_when_output_is_missing():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output=None,
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == 0.0
    assert result.feedback == "Actual output is missing."


@pytest.mark.asyncio
async def test_faithfulness_returns_zero_when_context_is_missing():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is the capital of France.",
        context=None,
    )

    assert result.score == 0.0
    assert result.feedback == "Context is missing from evaluation context."


@pytest.mark.asyncio
async def test_faithfulness_accepts_context_list():
    evaluator = FaithfulnessEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is the capital of France.",
        context={
            "context": [
                "Paris is the capital of France.",
                "France is in Europe.",
            ],
        },
    )

    assert result.score == pytest.approx(1.0)
    assert result.metadata["supported_tokens"] > 0


def test_faithfulness_metadata():
    evaluator = FaithfulnessEvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "faithfulness"

    assert metadata.description == (
        "Measures lexical support for model output terms against "
        "the supplied evaluation context using deterministic token matching."
    )

    assert metadata.requires_reference is False
    assert metadata.requires_context is True
    assert metadata.requires_llm is False
    assert metadata.applicable_to == ("text",)

    assert metadata.tags == (
        "deterministic",
        "context-based",
        "lexical",
        "faithfulness",
    )
