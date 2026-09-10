from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.model_gateway.google import GoogleModelProvider


@pytest.mark.asyncio
async def test_google_generate_returns_model_response():
    response = SimpleNamespace(
        text="Paris",
        usage_metadata=SimpleNamespace(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15,
        ),
    )

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.google.genai.Client",
        return_value=mock_client,
    ):
        provider = GoogleModelProvider(api_key="test-api-key")

        result = await provider.generate(
            prompt="What is the capital of France?",
            configuration={"model": "gemini-2.5-flash"},
        )

    assert result.output == "Paris"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.latency_ms >= 0
    assert result.trace["provider"] == "google"
    assert result.trace["model"] == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_google_generate_uses_model_configuration():
    response = SimpleNamespace(
        text="Hello",
        usage_metadata=SimpleNamespace(
            prompt_token_count=3,
            candidates_token_count=2,
            total_token_count=5,
        ),
    )

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.google.genai.Client",
        return_value=mock_client,
    ):
        provider = GoogleModelProvider(api_key="test-api-key")

        await provider.generate(
            prompt="Say hello.",
            configuration={"model": "custom-model"},
        )

    mock_client.aio.models.generate_content.assert_awaited_once_with(
        model="custom-model",
        contents="Say hello.",
    )


def test_google_generate_requires_api_key():
    with pytest.raises(
        ValueError,
        match="Google API key is not configured",
    ):
        GoogleModelProvider(api_key=None)


@pytest.mark.asyncio
async def test_google_generate_propagates_api_error():
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        side_effect=RuntimeError("Google request failed")
    )

    with patch(
        "app.services.model_gateway.google.genai.Client",
        return_value=mock_client,
    ):
        provider = GoogleModelProvider(api_key="test-api-key")

        with pytest.raises(
            RuntimeError,
            match="Google request failed",
        ):
            await provider.generate(
                prompt="Hello",
                configuration={"model": "gemini-2.5-flash"},
            )


@pytest.mark.asyncio
async def test_google_generate_handles_missing_usage():
    response = SimpleNamespace(
        text="Hello",
        usage_metadata=None,
    )

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.google.genai.Client",
        return_value=mock_client,
    ):
        provider = GoogleModelProvider(api_key="test-api-key")

        result = await provider.generate(
            prompt="Hello",
            configuration={"model": "gemini-2.5-flash"},
        )

    assert result.output == "Hello"
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.total_tokens == 0
    assert result.latency_ms >= 0
