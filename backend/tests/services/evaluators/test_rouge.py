import pytest

from app.services.evaluators.rouge import ROUGELvaluator


@pytest.mark.asyncio
async def test_rouge_l_returns_one_for_identical_output():
    evaluator = ROUGELvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris is the capital of France",
        actual_output="Paris is the capital of France",
    )

    assert result.metric == "rouge_l"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["lcs_length"] == 6
    assert result.metadata["precision"] == pytest.approx(1.0)
    assert result.metadata["recall"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_rouge_l_calculates_partial_sequence_overlap():
    evaluator = ROUGELvaluator()

    result = await evaluator.evaluate(
        expected_output="RAG combines retrieval and generation.",
        actual_output="RAG combines information.",
    )

    assert result.score == pytest.approx(0.5)
    assert result.metadata["lcs_length"] == 2
    assert result.metadata["precision"] == pytest.approx(2 / 3)
    assert result.metadata["recall"] == pytest.approx(2 / 5)


@pytest.mark.asyncio
async def test_rouge_l_handles_non_contiguous_sequence():
    evaluator = ROUGELvaluator()

    result = await evaluator.evaluate(
        expected_output="the cat is on the mat",
        actual_output="the cat sat on the mat",
    )

    assert result.metadata["lcs_length"] == 5
    assert result.metadata["precision"] == pytest.approx(5 / 6)
    assert result.metadata["recall"] == pytest.approx(5 / 6)
    assert result.score == pytest.approx(5 / 6)


@pytest.mark.asyncio
async def test_rouge_l_returns_zero_when_there_is_no_overlap():
    evaluator = ROUGELvaluator()

    result = await evaluator.evaluate(
        expected_output="Paris France",
        actual_output="Tokyo Japan",
    )

    assert result.score == 0.0
    assert result.metadata["lcs_length"] == 0
    assert result.metadata["precision"] == 0.0
    assert result.metadata["recall"] == 0.0
    assert result.feedback == ("No common subsequence between expected and actual output.")


@pytest.mark.asyncio
async def test_rouge_l_returns_zero_for_empty_output():
    evaluator = ROUGELvaluator()

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
async def test_rouge_l_returns_zero_when_output_is_missing(
    expected_output,
    actual_output,
):
    evaluator = ROUGELvaluator()

    result = await evaluator.evaluate(
        expected_output=expected_output,
        actual_output=actual_output,
    )

    assert result.score == 0.0
    assert result.feedback == ("Expected output or actual output is missing.")


def test_rouge_metadata():
    evaluator = ROUGELvaluator()

    metadata = evaluator.metadata

    assert metadata.category == "similarity"

    assert metadata.description == (
        "Measures longest common subsequence overlap between "
        "the model output and the reference answer using "
        "deterministic ROUGE-L scoring."
    )

    assert metadata.requires_reference is True
    assert metadata.requires_context is False
    assert metadata.requires_llm is False
    assert metadata.applicable_to == ("text",)

    assert metadata.tags == (
        "deterministic",
        "reference-based",
        "lcs",
        "rouge",
    )
