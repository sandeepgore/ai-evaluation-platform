from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.model_gateway.huggingface import (
    HuggingFaceModelProvider,
)


def make_response(
    *,
    content="Hello from Hugging Face",
    prompt_tokens=10,
    completion_tokens=5,
    total_tokens=15,
):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=content,
                )
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


@pytest.mark.asyncio
async def test_generate_uses_huggingface_chat_completion():
    provider = HuggingFaceModelProvider(
        api_key="test-key",
    )

    response = make_response()

    mock_create = AsyncMock(
        return_value=response,
    )

    with patch("app.services.model_gateway.huggingface.AsyncInferenceClient") as mock_client:
        mock_client.return_value.chat.completions.create = mock_create

        result = await provider.generate(
            prompt="Explain RAG",
            configuration={
                "model": "meta-llama/test-model",
                "provider": "hf-inference",
            },
        )

    mock_client.assert_called_once_with(
        model="meta-llama/test-model",
        provider="hf-inference",
        api_key="test-key",
        timeout=60,
    )

    mock_create.assert_awaited_once_with(
        messages=[
            {
                "role": "user",
                "content": "Explain RAG",
            }
        ],
        model="meta-llama/test-model",
        stream=False,
    )

    assert result.output == "Hello from Hugging Face"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.latency_ms >= 0

    assert result.trace == {
        "provider": "huggingface",
        "model": "meta-llama/test-model",
        "execution_mode": "hosted",
        "inference_provider": "hf-inference",
    }


@pytest.mark.asyncio
async def test_generate_supports_generation_configuration():
    provider = HuggingFaceModelProvider(
        api_key="test-key",
    )

    mock_create = AsyncMock(
        return_value=make_response(
            content='{"answer": "test"}',
        )
    )

    with patch("app.services.model_gateway.huggingface.AsyncInferenceClient") as mock_client:
        mock_client.return_value.chat.completions.create = mock_create

        result = await provider.generate(
            prompt="Return JSON",
            configuration={
                "model": "meta-llama/test-model",
                "provider": "groq",
                "timeout": 30,
                "temperature": 0.2,
                "max_tokens": 100,
                "response_format": "json",
            },
        )

    mock_client.assert_called_once_with(
        model="meta-llama/test-model",
        provider="groq",
        api_key="test-key",
        timeout=30,
    )

    mock_create.assert_awaited_once_with(
        messages=[
            {
                "role": "user",
                "content": "Return JSON",
            }
        ],
        model="meta-llama/test-model",
        stream=False,
        temperature=0.2,
        max_tokens=100,
        response_format={
            "type": "json_object",
        },
    )

    assert result.output == '{"answer": "test"}'


@pytest.mark.asyncio
async def test_generate_requires_model():
    provider = HuggingFaceModelProvider(
        api_key="test-key",
    )

    with pytest.raises(
        ValueError,
        match="Hugging Face model identifier is required",
    ):
        await provider.generate(
            prompt="Hello",
            configuration={},
        )


@pytest.mark.asyncio
async def test_generate_propagates_huggingface_error():
    provider = HuggingFaceModelProvider(
        api_key="test-key",
    )

    mock_create = AsyncMock(
        side_effect=RuntimeError("HF request failed"),
    )

    with patch("app.services.model_gateway.huggingface.AsyncInferenceClient") as mock_client:
        mock_client.return_value.chat.completions.create = mock_create

        with pytest.raises(
            RuntimeError,
            match="HF request failed",
        ):
            await provider.generate(
                prompt="Hello",
                configuration={
                    "model": "meta-llama/test-model",
                },
            )


@pytest.mark.asyncio
async def test_generate_local_uses_openai_compatible_server():
    provider = HuggingFaceModelProvider()

    response = make_response(
        content="local response",
    )

    mock_create = AsyncMock(
        return_value=response,
    )

    with patch("app.services.model_gateway.huggingface.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = mock_create

        result = await provider.generate(
            prompt="hello",
            configuration={
                "model": "meta-llama/Llama-3.2-3B-Instruct",
                "mode": "local",
                "runtime": "vllm",
                "base_url": "http://localhost:8000/v1",
            },
        )

    mock_openai.assert_called_once_with(
        api_key="local",
        base_url="http://localhost:8000/v1",
        timeout=60,
    )

    mock_create.assert_awaited_once_with(
        messages=[
            {
                "role": "user",
                "content": "hello",
            }
        ],
        model="meta-llama/Llama-3.2-3B-Instruct",
        stream=False,
    )

    assert result.output == "local response"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.trace == {
        "provider": "huggingface",
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "execution_mode": "local",
    }


@pytest.mark.asyncio
async def test_generate_endpoint_uses_configured_endpoint():
    provider = HuggingFaceModelProvider(
        api_key="test-hf-key",
    )

    response = make_response(
        content="endpoint response",
    )

    mock_create = AsyncMock(
        return_value=response,
    )

    with patch("app.services.model_gateway.huggingface.AsyncInferenceClient") as mock_hf:
        mock_hf.return_value.chat.completions.create = mock_create

        result = await provider.generate(
            prompt="hello",
            configuration={
                "model": "my-model",
                "mode": "endpoint",
                "base_url": "https://example-endpoint",
            },
        )

    mock_hf.assert_called_once_with(
        model="my-model",
        provider="hf-inference",
        api_key="test-hf-key",
        base_url="https://example-endpoint",
        timeout=60,
    )

    assert result.output == "endpoint response"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.trace == {
        "provider": "huggingface",
        "model": "my-model",
        "execution_mode": "endpoint",
        "inference_provider": "hf-inference",
    }


@pytest.mark.asyncio
async def test_local_requires_base_url():
    provider = HuggingFaceModelProvider()

    with pytest.raises(
        ValueError,
        match="local execution requires 'base_url'",
    ):
        await provider.generate(
            prompt="hello",
            configuration={
                "model": "local-model",
                "mode": "local",
            },
        )


@pytest.mark.asyncio
async def test_endpoint_requires_base_url():
    provider = HuggingFaceModelProvider()

    with pytest.raises(
        ValueError,
        match="endpoint execution requires 'base_url'",
    ):
        await provider.generate(
            prompt="hello",
            configuration={
                "model": "remote-model",
                "mode": "endpoint",
            },
        )


@pytest.mark.asyncio
async def test_local_model_unavailable_returns_clear_error():
    provider = HuggingFaceModelProvider()

    mock_create = AsyncMock(
        side_effect=ConnectionError(
            "Connection refused",
        ),
    )

    with patch("app.services.model_gateway.huggingface.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = mock_create

        with pytest.raises(
            RuntimeError,
            match=("Hugging Face model 'local-model' could not be invoked using local execution"),
        ):
            await provider.generate(
                prompt="hello",
                configuration={
                    "model": "local-model",
                    "mode": "local",
                    "base_url": "http://localhost:8000/v1",
                },
            )


@pytest.mark.asyncio
async def test_endpoint_model_unavailable_returns_clear_error():
    provider = HuggingFaceModelProvider(
        api_key="test-key",
    )

    mock_create = AsyncMock(
        side_effect=ConnectionError(
            "Endpoint unavailable",
        ),
    )

    with patch("app.services.model_gateway.huggingface.AsyncInferenceClient") as mock_hf:
        mock_hf.return_value.chat.completions.create = mock_create

        with pytest.raises(
            RuntimeError,
            match=(
                "Hugging Face model 'endpoint-model' could not be invoked using endpoint execution"
            ),
        ):
            await provider.generate(
                prompt="hello",
                configuration={
                    "model": "endpoint-model",
                    "mode": "endpoint",
                    "base_url": "https://example-endpoint",
                },
            )


@pytest.mark.asyncio
async def test_unsupported_execution_mode_is_rejected():
    provider = HuggingFaceModelProvider()

    with pytest.raises(
        ValueError,
        match="Unsupported Hugging Face execution mode",
    ):
        await provider.generate(
            prompt="hello",
            configuration={
                "model": "some-model",
                "mode": "something-else",
            },
        )
