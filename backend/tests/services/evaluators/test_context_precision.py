import pytest

from app.services.evaluators import ContextPrecisionEvaluator


@pytest.mark.asyncio
async def test_context_precision_returns_one_when_context_is_fully_supported():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.metric == "context_precision"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["overlap_tokens"] == 3


@pytest.mark.asyncio
async def test_context_precision_calculates_partial_overlap():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Paris is the capital of France and Europe.",
        },
    )

    assert 0.0 < result.score < 1.0
    assert result.metadata["overlap_tokens"] > 0
    assert result.metadata["overlap_tokens"] < result.metadata["context_token_count"]


@pytest.mark.asyncio
async def test_context_precision_returns_zero_when_context_is_not_supported():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Tokyo is located in Japan.",
        },
    )

    assert result.score == 0.0
    assert result.metadata["overlap_tokens"] == 0


@pytest.mark.asyncio
async def test_context_precision_ignores_case_and_punctuation():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France!",
        actual_output=None,
        context={
            "context": "PARIS, capital, FRANCE.",
        },
    )

    assert result.score == pytest.approx(3 / 3)


@pytest.mark.asyncio
async def test_context_precision_does_not_require_actual_output():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_context_precision_returns_zero_when_reference_is_missing():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output=None,
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == 0.0
    assert result.feedback == "Expected output is missing."


@pytest.mark.asyncio
async def test_context_precision_returns_zero_when_context_is_missing():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context=None,
    )

    assert result.score == 0.0
    assert result.feedback == "Context is missing from evaluation context."


@pytest.mark.asyncio
async def test_context_precision_accepts_context_list():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": [
                "Paris is the capital of France.",
                "France is in Europe.",
            ],
        },
    )

    assert 0.0 < result.score < 1.0


@pytest.mark.asyncio
async def test_context_precision_accepts_reference_context_key():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "reference_context": "Paris is the capital of France.",
        },
    )

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_context_precision_removes_stopwords():
    evaluator = ContextPrecisionEvaluator()

    result = await evaluator.evaluate(
        expected_output="capital France",
        actual_output=None,
        context={
            "context": "What is the capital of France?",
        },
    )

    assert result.score == pytest.approx(1.0)
    assert result.metadata["context_tokens"] == ["capital", "france"]


def test_context_precision_metadata():
    evaluator = ContextPrecisionEvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "context_precision"

    assert metadata.description == (
        "Measures lexical precision of meaningful context terms "
        "against the expected reference answer."
    )

    assert metadata.requires_reference is True
    assert metadata.requires_context is True
    assert metadata.requires_supporting_context is True
    assert metadata.requires_llm is False
    assert metadata.applicable_to == ("rag",)

    assert metadata.tags == (
        "deterministic",
        "context-based",
        "lexical",
        "retrieval",
        "precision",
    )
