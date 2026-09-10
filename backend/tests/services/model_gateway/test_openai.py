from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.model_gateway.openai import OpenAIModelProvider


@pytest.mark.asyncio
async def test_openai_generate_returns_model_response():
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(content="Paris"),
        )
    ]
    response.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.openai.AsyncOpenAI",
        return_value=mock_client,
    ):
        provider = OpenAIModelProvider(api_key="test-api-key")

        result = await provider.generate(
            prompt="What is the capital of France?",
            configuration={"model": "gpt-4o"},
        )

    assert result.output == "Paris"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.latency_ms >= 0
    assert result.trace["provider"] == "openai"
    assert result.trace["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_openai_generate_uses_model_configuration():
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(content="Hello"),
        )
    ]
    response.usage = MagicMock(
        prompt_tokens=3,
        completion_tokens=2,
        total_tokens=5,
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.openai.AsyncOpenAI",
        return_value=mock_client,
    ):
        provider = OpenAIModelProvider(api_key="test-api-key")

        await provider.generate(
            prompt="Say hello.",
            configuration={"model": "custom-model"},
        )

    mock_client.chat.completions.create.assert_awaited_once_with(
        model="custom-model",
        messages=[
            {
                "role": "user",
                "content": "Say hello.",
            }
        ],
    )


def test_openai_generate_requires_api_key():
    with pytest.raises(ValueError, match="OpenAI API key is not configured"):
        OpenAIModelProvider(api_key=None)


@pytest.mark.asyncio
async def test_openai_generate_propagates_api_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("OpenAI request failed")
    )

    with patch(
        "app.services.model_gateway.openai.AsyncOpenAI",
        return_value=mock_client,
    ):
        provider = OpenAIModelProvider(api_key="test-api-key")

        with pytest.raises(RuntimeError, match="OpenAI request failed"):
            await provider.generate(
                prompt="Hello",
                configuration={"model": "gpt-4o"},
            )


@pytest.mark.asyncio
async def test_openai_generate_handles_missing_usage():
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(content="Hello"),
        )
    ]
    response.usage = None

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.openai.AsyncOpenAI",
        return_value=mock_client,
    ):
        provider = OpenAIModelProvider(api_key="test-api-key")

        result = await provider.generate(
            prompt="Hello",
            configuration={"model": "gpt-4o"},
        )

    assert result.output == "Hello"
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.total_tokens == 0
    assert result.latency_ms >= 0
