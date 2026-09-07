import pytest

from app.services.evaluators import ContextRecallEvaluator


@pytest.mark.asyncio
async def test_context_recall_returns_one_when_reference_is_fully_supported():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.metric == "context_recall"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["overlap_tokens"] == 3


@pytest.mark.asyncio
async def test_context_recall_calculates_partial_overlap():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Paris is a city in Europe.",
        },
    )

    assert 0.0 < result.score < 1.0
    assert result.metadata["overlap_tokens"] > 0
    assert result.metadata["overlap_tokens"] < result.metadata["reference_token_count"]


@pytest.mark.asyncio
async def test_context_recall_returns_zero_when_reference_is_not_supported():
    evaluator = ContextRecallEvaluator()

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
async def test_context_recall_ignores_case_and_punctuation():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France!",
        actual_output=None,
        context={
            "context": "PARIS, capital, FRANCE.",
        },
    )

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_context_recall_does_not_require_actual_output():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "context": "Paris is the capital of France.",
        },
    )

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_context_recall_returns_zero_when_reference_is_missing():
    evaluator = ContextRecallEvaluator()

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
async def test_context_recall_returns_zero_when_context_is_missing():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context=None,
    )

    assert result.score == 0.0
    assert result.feedback == "Context is missing from evaluation context."


@pytest.mark.asyncio
async def test_context_recall_accepts_context_list():
    evaluator = ContextRecallEvaluator()

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

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_context_recall_accepts_retrieved_context_key():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France.",
        actual_output=None,
        context={
            "retrieved_context": "Paris is the capital of France.",
        },
    )

    assert result.score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_context_recall_removes_stopwords():
    evaluator = ContextRecallEvaluator()

    result = await evaluator.evaluate(
        expected_output="What is the capital of France?",
        actual_output=None,
        context={
            "context": "capital France",
        },
    )

    assert result.score == pytest.approx(1.0)
    assert result.metadata["reference_tokens"] == ["capital", "france"]


def test_context_recall_metadata():
    evaluator = ContextRecallEvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "context_recall"

    assert metadata.description == (
        "Measures lexical coverage of meaningful reference answer "
        "terms in the supplied evaluation context."
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
        "recall",
    )
