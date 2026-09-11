from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.model_gateway.azure_openai import (
    AzureOpenAIModelProvider,
)


def make_response(
    *,
    content="Hello from Azure",
    prompt_tokens=10,
    completion_tokens=5,
    total_tokens=15,
):
    return MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=content,
                )
            )
        ],
        usage=MagicMock(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


@pytest.mark.asyncio
async def test_azure_openai_generate_returns_model_response():
    response = make_response()

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.azure_openai.AsyncAzureOpenAI",
        return_value=mock_client,
    ) as mock_azure_client:
        provider = AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )

        result = await provider.generate(
            prompt="Say hello.",
            configuration={
                "model": "test-deployment",
            },
        )

    mock_azure_client.assert_called_once_with(
        api_key="test-api-key",
        azure_endpoint="https://test.openai.azure.com/",
        api_version="2024-10-21",
        timeout=60,
    )

    assert result.output == "Hello from Azure"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.latency_ms >= 0
    assert result.trace["provider"] == "azure_openai"
    assert result.trace["model"] == "test-deployment"
    assert result.trace["api_version"] == "2024-10-21"


@pytest.mark.asyncio
async def test_azure_openai_generate_uses_model_configuration():
    response = make_response(
        content="Configured response",
        prompt_tokens=3,
        completion_tokens=2,
        total_tokens=5,
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.azure_openai.AsyncAzureOpenAI",
        return_value=mock_client,
    ):
        provider = AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )

        await provider.generate(
            prompt="Hello",
            configuration={
                "model": "custom-deployment",
                "api_version": "2025-04-01-preview",
                "temperature": 0.2,
                "max_tokens": 100,
            },
        )

    mock_client.chat.completions.create.assert_awaited_once_with(
        model="custom-deployment",
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
        temperature=0.2,
        max_tokens=100,
    )


@pytest.mark.asyncio
async def test_azure_openai_generate_supports_json_response_format():
    response = make_response()

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.azure_openai.AsyncAzureOpenAI",
        return_value=mock_client,
    ):
        provider = AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )

        await provider.generate(
            prompt="Return JSON.",
            configuration={
                "model": "test-deployment",
                "response_format": "json",
            },
        )

    mock_client.chat.completions.create.assert_awaited_once_with(
        model="test-deployment",
        messages=[
            {
                "role": "user",
                "content": "Return JSON.",
            }
        ],
        response_format={
            "type": "json_object",
        },
    )


def test_azure_openai_generate_requires_api_key():
    with pytest.raises(
        ValueError,
        match="Azure OpenAI API key is not configured",
    ):
        AzureOpenAIModelProvider(
            api_key=None,
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )


def test_azure_openai_generate_requires_endpoint():
    with pytest.raises(
        ValueError,
        match="Azure OpenAI endpoint is not configured",
    ):
        AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint=None,
            api_version="2024-10-21",
        )


@pytest.mark.asyncio
async def test_azure_openai_generate_requires_model():
    provider = AzureOpenAIModelProvider(
        api_key="test-api-key",
        endpoint="https://test.openai.azure.com/",
        api_version="2024-10-21",
    )

    with pytest.raises(
        ValueError,
        match="Azure OpenAI deployment name is required",
    ):
        await provider.generate(
            prompt="Hello",
            configuration={},
        )


@pytest.mark.asyncio
async def test_azure_openai_generate_requires_api_version():
    provider = AzureOpenAIModelProvider(
        api_key="test-api-key",
        endpoint="https://test.openai.azure.com/",
        api_version=None,
    )

    with pytest.raises(
        ValueError,
        match="Azure OpenAI API version is required",
    ):
        await provider.generate(
            prompt="Hello",
            configuration={
                "model": "test-deployment",
            },
        )


@pytest.mark.asyncio
async def test_azure_openai_generate_uses_configuration_api_version():
    response = make_response()

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.azure_openai.AsyncAzureOpenAI",
        return_value=mock_client,
    ) as mock_azure_client:
        provider = AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )

        await provider.generate(
            prompt="Hello",
            configuration={
                "model": "test-deployment",
                "api_version": "2025-04-01-preview",
            },
        )

    mock_azure_client.assert_called_once_with(
        api_key="test-api-key",
        azure_endpoint="https://test.openai.azure.com/",
        api_version="2025-04-01-preview",
        timeout=60,
    )


@pytest.mark.asyncio
async def test_azure_openai_generate_rejects_unsupported_response_format():
    provider = AzureOpenAIModelProvider(
        api_key="test-api-key",
        endpoint="https://test.openai.azure.com/",
        api_version="2024-10-21",
    )

    with pytest.raises(
        ValueError,
        match="Only 'json' response format is supported",
    ):
        await provider.generate(
            prompt="Hello",
            configuration={
                "model": "test-deployment",
                "response_format": "text",
            },
        )


@pytest.mark.asyncio
async def test_azure_openai_generate_propagates_api_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("Azure request failed")
    )

    with patch(
        "app.services.model_gateway.azure_openai.AsyncAzureOpenAI",
        return_value=mock_client,
    ):
        provider = AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )

        with pytest.raises(
            RuntimeError,
            match="Azure OpenAI deployment 'test-deployment' could not be invoked",
        ):
            await provider.generate(
                prompt="Hello",
                configuration={
                    "model": "test-deployment",
                },
            )


@pytest.mark.asyncio
async def test_azure_openai_generate_handles_missing_usage():
    response = make_response()
    response.usage = None

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch(
        "app.services.model_gateway.azure_openai.AsyncAzureOpenAI",
        return_value=mock_client,
    ):
        provider = AzureOpenAIModelProvider(
            api_key="test-api-key",
            endpoint="https://test.openai.azure.com/",
            api_version="2024-10-21",
        )

        result = await provider.generate(
            prompt="Hello",
            configuration={
                "model": "test-deployment",
            },
        )

    assert result.output == "Hello from Azure"
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.total_tokens == 0
