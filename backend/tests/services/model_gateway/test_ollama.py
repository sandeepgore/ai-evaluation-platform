from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.model_gateway.ollama import OllamaModelProvider


@pytest.mark.asyncio
async def test_ollama_generate_returns_model_response():
    provider = OllamaModelProvider()

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "message": {"content": "Paris is the capital of France."},
        "prompt_eval_count": 10,
        "eval_count": 7,
        "done_reason": "stop",
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = response

    with patch(
        "app.services.model_gateway.ollama.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await provider.generate(prompt="What is the capital of France?")

    assert result.output == "Paris is the capital of France."
    assert result.input_tokens == 10
    assert result.output_tokens == 7
    assert result.total_tokens == 17
    assert result.latency_ms >= 0

    assert result.trace["provider"] == "ollama"
    assert result.trace["model"] == "llama3.2:3b"
    assert result.trace["done_reason"] == "stop"


@pytest.mark.asyncio
async def test_ollama_generate_uses_custom_configuration():
    provider = OllamaModelProvider()

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "message": {"content": "Hello"},
        "prompt_eval_count": 5,
        "eval_count": 3,
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = response

    with patch(
        "app.services.model_gateway.ollama.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await provider.generate(
            prompt="Say hello",
            configuration={
                "base_url": "http://localhost:11434/",
                "model": "llama3.2:1b",
                "timeout": 30,
            },
        )

    mock_client.post.assert_awaited_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2:1b",
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello",
                }
            ],
            "stream": False,
        },
    )

    assert result.output == "Hello"
    assert result.trace["model"] == "llama3.2:1b"
    assert result.trace["base_url"] == "http://localhost:11434"


@pytest.mark.asyncio
async def test_ollama_generate_calls_raise_for_status():
    provider = OllamaModelProvider()

    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error",
        request=MagicMock(),
        response=MagicMock(),
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = response

    with patch(
        "app.services.model_gateway.ollama.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(httpx.HTTPStatusError):
            await provider.generate(prompt="Hello")

    response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_ollama_generate_propagates_connection_error():
    provider = OllamaModelProvider()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = httpx.ConnectError("Unable to connect to Ollama")

    with patch(
        "app.services.model_gateway.ollama.httpx.AsyncClient",
        return_value=mock_client,
    ):
        with pytest.raises(httpx.ConnectError):
            await provider.generate(prompt="Hello")


@pytest.mark.asyncio
async def test_ollama_generate_handles_missing_message():
    provider = OllamaModelProvider()

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "prompt_eval_count": 4,
        "eval_count": 2,
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = response

    with patch(
        "app.services.model_gateway.ollama.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await provider.generate(prompt="Hello")

    assert result.output == ""
    assert result.input_tokens == 4
    assert result.output_tokens == 2
    assert result.total_tokens == 6
