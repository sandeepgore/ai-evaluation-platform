import pytest

from app.services.evaluators import RelevanceEvaluator


@pytest.mark.asyncio
async def test_relevance_returns_one_when_all_query_terms_are_present():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="The capital of France is Paris.",
        context={"input": "What is the capital of France?"},
    )

    assert result.metric == "relevance"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["overlap_tokens"] == 2


@pytest.mark.asyncio
async def test_relevance_calculates_partial_overlap():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is a city in France.",
        context={"input": "What is the capital of France?"},
    )

    assert result.score == pytest.approx(1 / 2)
    assert result.metadata["overlap_tokens"] == 1


@pytest.mark.asyncio
async def test_relevance_returns_zero_when_there_is_no_overlap():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Tokyo is in Japan.",
        context={"input": "What is the capital of France?"},
    )

    assert result.score == 0.0
    assert result.metadata["overlap_tokens"] == 0


@pytest.mark.asyncio
async def test_relevance_ignores_case_and_punctuation():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="FRANCE! Paris.",
        context={"input": "France Paris"},
    )

    assert result.score == pytest.approx(1.0)
    assert result.metadata["overlap_tokens"] == 2


@pytest.mark.asyncio
async def test_relevance_returns_zero_for_empty_output():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="   ",
        context={"input": "What is the capital of France?"},
    )

    assert result.score == 0.0
    assert result.feedback == "Input or actual output is empty."


@pytest.mark.asyncio
async def test_relevance_returns_zero_when_output_is_missing():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output=None,
        context={"input": "What is the capital of France?"},
    )

    assert result.score == 0.0
    assert result.feedback == "Actual output is missing."


@pytest.mark.asyncio
async def test_relevance_returns_zero_when_context_is_missing():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is the capital of France.",
        context=None,
    )

    assert result.score == 0.0
    assert result.feedback == ("Input or query is missing from evaluation context.")


@pytest.mark.asyncio
async def test_relevance_accepts_query_context_key():
    evaluator = RelevanceEvaluator()

    result = await evaluator.evaluate(
        expected_output=None,
        actual_output="Paris is the capital of France.",
        context={"query": "What is the capital of France?"},
    )

    assert result.score == pytest.approx(1.0)
    assert result.metadata["overlap_tokens"] == 2


def test_relevance_metadata():
    evaluator = RelevanceEvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "relevance"

    assert metadata.description == (
        "Measures lexical coverage of meaningful query terms "
        "in the model output using deterministic token overlap."
    )

    assert metadata.requires_reference is False
    assert metadata.requires_context is True
    assert metadata.requires_llm is False
    assert metadata.applicable_to == ("rag",)

    assert metadata.tags == (
        "deterministic",
        "context-based",
        "lexical",
        "relevance",
    )
