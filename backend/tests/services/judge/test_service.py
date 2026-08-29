from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.model_gateway import ModelResponse
from app.services.judge import JudgeConfiguration, JudgeService


def make_configuration(
    **overrides,
) -> JudgeConfiguration:
    configuration = {
        "provider": "ollama",
        "model": "llama3.2:3b",
        "criteria": "Evaluate correctness.",
        "min_score": 0.0,
        "max_score": 1.0,
    }

    configuration.update(overrides)

    return JudgeConfiguration(**configuration)


def make_service(
    *,
    model_gateway=None,
    **configuration_overrides,
) -> JudgeService:
    gateway = model_gateway or MagicMock()

    return JudgeService(
        model_gateway=gateway,
        configuration=make_configuration(
            **configuration_overrides,
        ),
    )


# ----------------------------------------------------------------------
# Response parsing
# ----------------------------------------------------------------------


def test_parse_plain_json():
    service = make_service()

    result = service._parse_response(
        '{"score": 0.8, "feedback": "Good answer.", "reasoning": "Correct."}'
    )

    assert result.score == pytest.approx(0.8)
    assert result.feedback == "Good answer."
    assert result.reasoning == "Correct."


def test_parse_json_code_fence():
    service = make_service()

    result = service._parse_response(
        """```json
{
    "score": 0.8,
    "feedback": "Good answer.",
    "reasoning": "Correct."
}
```"""
    )

    assert result.score == pytest.approx(0.8)
    assert result.feedback == "Good answer."
    assert result.reasoning == "Correct."


def test_parse_generic_code_fence():
    service = make_service()

    result = service._parse_response(
        """```
{
    "score": 0.7,
    "feedback": "Acceptable.",
    "reasoning": "Mostly correct."
}
```"""
    )

    assert result.score == pytest.approx(0.7)
    assert result.feedback == "Acceptable."


def test_parse_json_surrounded_by_text():
    service = make_service()

    result = service._parse_response(
        """Here is the evaluation:

{
    "score": 0.9,
    "feedback": "Excellent.",
    "reasoning": "The answer is correct."
}

Hope this helps."""
    )

    assert result.score == pytest.approx(0.9)
    assert result.feedback == "Excellent."
    assert result.reasoning == "The answer is correct."


def test_parse_embedded_json_with_braces_inside_string():
    service = make_service()

    result = service._parse_response(
        """The evaluation result is:

{
    "score": 0.85,
    "feedback": "The response contains {important} information.",
    "reasoning": "The structure {A -> B} is correct."
}

End of evaluation."""
    )

    assert result.score == pytest.approx(0.85)
    assert result.feedback == ("The response contains {important} information.")
    assert result.reasoning == ("The structure {A -> B} is correct.")


def test_parse_rejects_invalid_json():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        service._parse_response("This is not a valid judge response.")


def test_parse_rejects_non_object_json():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="JSON object",
    ):
        service._parse_response('[{"score": 0.8}]')


def test_parse_rejects_missing_score():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="score.*number",
    ):
        service._parse_response('{"feedback": "Good answer."}')


def test_parse_rejects_boolean_score():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="score.*number",
    ):
        service._parse_response('{"score": true}')


def test_parse_rejects_score_above_range():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        service._parse_response('{"score": 1.5}')


def test_parse_rejects_score_below_range():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        service._parse_response('{"score": -0.1}')


def test_parse_empty_response():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="empty response",
    ):
        service._parse_response("   ")


def test_parse_converts_non_string_feedback():
    service = make_service()

    result = service._parse_response('{"score": 0.8, "feedback": 123, "reasoning": 456}')

    assert result.feedback == "123"
    assert result.reasoning == "456"


def test_parse_optional_feedback_and_reasoning():
    service = make_service()

    result = service._parse_response('{"score": 0.8}')

    assert result.score == pytest.approx(0.8)
    assert result.feedback is None
    assert result.reasoning is None


def test_parse_preserves_raw_output():
    service = make_service()

    raw_output = """```json
{
    "score": 0.8,
    "feedback": "Good.",
    "reasoning": "Correct."
}
```"""

    result = service._parse_response(raw_output)

    assert result.raw_output == raw_output


def test_parse_adds_judge_metadata():
    service = make_service(
        provider="ollama",
        model="llama3.2:3b",
    )

    result = service._parse_response('{"score": 0.8}')

    assert result.metadata == {
        "judge_model": "llama3.2:3b",
        "judge_provider": "ollama",
    }


# ----------------------------------------------------------------------
# Prompt construction
# ----------------------------------------------------------------------


def test_build_prompt_contains_evaluation_inputs():
    service = make_service(
        criteria="Evaluate correctness and relevance.",
    )

    prompt = service._build_prompt(
        input_text="What is the capital of France?",
        expected_output="Paris",
        actual_output="Paris is the capital of France.",
        context="France has Paris as its capital.",
    )

    assert "Evaluate correctness and relevance." in prompt
    assert "What is the capital of France?" in prompt
    assert "Paris" in prompt
    assert "Paris is the capital of France." in prompt
    assert "France has Paris as its capital." in prompt


def test_build_prompt_handles_missing_optional_values():
    service = make_service()

    prompt = service._build_prompt(
        input_text=None,
        expected_output=None,
        actual_output="Paris",
        context=None,
    )

    assert "No input was provided." in prompt
    assert "No expected output was provided." in prompt
    assert "No context was provided." in prompt
    assert "Paris" in prompt


def test_serialize_context_preserves_strings():
    result = JudgeService._serialize_context("Paris is the capital of France.")

    assert result == "Paris is the capital of France."


def test_serialize_context_serializes_structured_data():
    result = JudgeService._serialize_context(
        {
            "documents": [
                "Paris is the capital of France.",
                "France is in Europe.",
            ]
        }
    )

    assert "Paris is the capital of France." in result
    assert "France is in Europe." in result


# ----------------------------------------------------------------------
# JudgeService.evaluate()
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_calls_model_gateway():
    gateway = MagicMock()

    gateway.generate = AsyncMock(
        return_value=ModelResponse(
            output=('{"score": 0.9, "feedback": "Excellent.", "reasoning": "Correct answer."}'),
        )
    )

    service = make_service(
        model_gateway=gateway,
    )

    result = await service.evaluate(
        input_text="What is the capital of France?",
        expected_output="Paris",
        actual_output="Paris",
        context="Paris is the capital of France.",
    )

    assert result.score == pytest.approx(0.9)
    assert result.feedback == "Excellent."
    assert result.reasoning == "Correct answer."

    gateway.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_evaluate_passes_model_configuration_to_gateway():
    gateway = MagicMock()

    gateway.generate = AsyncMock(
        return_value=ModelResponse(
            output='{"score": 0.8}',
        )
    )

    service = make_service(
        model_gateway=gateway,
        model="llama3.2:3b",
        timeout=30.0,
        temperature=0.2,
        base_url="http://localhost:11434",
    )

    await service.evaluate(
        actual_output="Paris",
    )

    gateway.generate.assert_awaited_once()

    call = gateway.generate.await_args
    configuration = call.kwargs["configuration"]

    assert configuration["model"] == "llama3.2:3b"
    assert configuration["timeout"] == 30.0
    assert configuration["temperature"] == 0.2
    assert configuration["base_url"] == "http://localhost:11434"
    assert configuration["response_format"] == "json"


@pytest.mark.asyncio
async def test_evaluate_rejects_empty_actual_output():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="Actual output must not be empty",
    ):
        await service.evaluate(
            actual_output="",
        )


@pytest.mark.asyncio
async def test_evaluate_rejects_whitespace_only_actual_output():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="Actual output must not be empty",
    ):
        await service.evaluate(
            actual_output="   ",
        )


@pytest.mark.asyncio
async def test_evaluate_propagates_gateway_error():
    gateway = MagicMock()

    gateway.generate = AsyncMock(side_effect=RuntimeError("Model unavailable"))

    service = make_service(
        model_gateway=gateway,
    )

    with pytest.raises(
        RuntimeError,
        match="Model unavailable",
    ):
        await service.evaluate(
            actual_output="Paris",
        )
