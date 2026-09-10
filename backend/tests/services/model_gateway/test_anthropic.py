from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.model_gateway.anthropic import AnthropicModelProvider


@pytest.mark.asyncio
async def test_anthropic_generate_returns_model_response():
    response = MagicMock()
    response.content = [
        MagicMock(text="Paris"),
    ]
    response.usage = MagicMock(
        input_tokens=10,
        output_tokens=5,
    )

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.anthropic.AsyncAnthropic",
        return_value=mock_client,
    ):
        provider = AnthropicModelProvider(api_key="test-api-key")

        result = await provider.generate(
            prompt="What is the capital of France?",
            configuration={"model": "claude-sonnet-4-5"},
        )

    assert result.output == "Paris"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.latency_ms >= 0
    assert result.trace["provider"] == "anthropic"
    assert result.trace["model"] == "claude-sonnet-4-5"


@pytest.mark.asyncio
async def test_anthropic_generate_uses_model_configuration():
    response = MagicMock()
    response.content = [
        MagicMock(text="Hello"),
    ]
    response.usage = MagicMock(
        input_tokens=3,
        output_tokens=2,
    )

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.anthropic.AsyncAnthropic",
        return_value=mock_client,
    ):
        provider = AnthropicModelProvider(api_key="test-api-key")

        await provider.generate(
            prompt="Say hello.",
            configuration={"model": "custom-model"},
        )

    mock_client.messages.create.assert_awaited_once_with(
        model="custom-model",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Say hello.",
            }
        ],
    )


def test_anthropic_generate_requires_api_key():
    with pytest.raises(
        ValueError,
        match="Anthropic API key is not configured",
    ):
        AnthropicModelProvider(api_key=None)


@pytest.mark.asyncio
async def test_anthropic_generate_propagates_api_error():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=RuntimeError("Anthropic request failed"))

    with patch(
        "app.services.model_gateway.anthropic.AsyncAnthropic",
        return_value=mock_client,
    ):
        provider = AnthropicModelProvider(api_key="test-api-key")

        with pytest.raises(
            RuntimeError,
            match="Anthropic request failed",
        ):
            await provider.generate(
                prompt="Hello",
                configuration={"model": "claude-sonnet-4-5"},
            )


@pytest.mark.asyncio
async def test_anthropic_generate_handles_missing_usage():
    response = MagicMock()
    response.content = [
        MagicMock(text="Hello"),
    ]
    response.usage = None

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.anthropic.AsyncAnthropic",
        return_value=mock_client,
    ):
        provider = AnthropicModelProvider(api_key="test-api-key")

        result = await provider.generate(
            prompt="Hello",
            configuration={"model": "claude-sonnet-4-5"},
        )

    assert result.output == "Hello"
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.total_tokens == 0
    assert result.latency_ms >= 0
