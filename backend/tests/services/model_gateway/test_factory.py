from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.model_gateway.azure_openai import AzureOpenAIModelProvider
from app.models.model import ModelProvider
from app.services.model_gateway.anthropic import AnthropicModelProvider
from app.services.model_gateway.factory import ModelGatewayFactory
from app.services.model_gateway.google import GoogleModelProvider
from app.services.model_gateway.huggingface import HuggingFaceModelProvider
from app.services.model_gateway.mock import MockModelProvider
from app.services.model_gateway.ollama import OllamaModelProvider
from app.services.model_gateway.openai import OpenAIModelProvider


def test_factory_creates_mock_provider():
    model = SimpleNamespace(
        provider=ModelProvider.MOCK,
    )

    gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, MockModelProvider)


def test_factory_creates_ollama_provider():
    model = SimpleNamespace(
        provider=ModelProvider.OLLAMA,
    )

    gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, OllamaModelProvider)


def test_factory_creates_openai_provider():
    model = SimpleNamespace(
        provider=ModelProvider.OPENAI,
    )

    with patch(
        "app.services.model_gateway.factory.settings.openai_api_key",
        "test-openai-key",
    ):
        gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, OpenAIModelProvider)


def test_factory_rejects_openai_when_api_key_is_missing():
    model = SimpleNamespace(
        provider=ModelProvider.OPENAI,
    )

    with patch(
        "app.services.model_gateway.factory.settings.openai_api_key",
        None,
    ):
        with pytest.raises(
            ValueError,
            match="OpenAI API key is not configured",
        ):
            ModelGatewayFactory.create(model)


@pytest.mark.parametrize(
    "provider",
    [
        ModelProvider.CUSTOM,
    ],
)
def test_factory_rejects_unimplemented_provider(provider):
    model = SimpleNamespace(
        provider=provider,
    )

    with pytest.raises(ValueError):
        ModelGatewayFactory.create(model)


def test_factory_creates_anthropic_provider():
    model = SimpleNamespace(
        provider=ModelProvider.ANTHROPIC,
    )

    with patch(
        "app.services.model_gateway.factory.settings.anthropic_api_key",
        "test-anthropic-key",
    ):
        gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, AnthropicModelProvider)


def test_factory_rejects_anthropic_when_api_key_is_missing():
    model = SimpleNamespace(
        provider=ModelProvider.ANTHROPIC,
    )

    with patch(
        "app.services.model_gateway.factory.settings.anthropic_api_key",
        None,
    ):
        with pytest.raises(
            ValueError,
            match="Anthropic API key is not configured",
        ):
            ModelGatewayFactory.create(model)


def test_factory_creates_google_provider():
    model = SimpleNamespace(
        provider=ModelProvider.GOOGLE,
    )

    with patch(
        "app.services.model_gateway.factory.settings.google_api_key",
        "test-google-key",
    ):
        gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, GoogleModelProvider)


def test_factory_rejects_google_when_api_key_is_missing():
    model = SimpleNamespace(
        provider=ModelProvider.GOOGLE,
    )

    with patch(
        "app.services.model_gateway.factory.settings.google_api_key",
        None,
    ):
        with pytest.raises(
            ValueError,
            match="Google API key is not configured",
        ):
            ModelGatewayFactory.create(model)


def test_factory_creates_huggingface_provider():
    model = SimpleNamespace(
        provider=ModelProvider.HUGGINGFACE,
    )

    with patch(
        "app.services.model_gateway.factory.settings.huggingface_api_key",
        "test-huggingface-key",
    ):
        gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, HuggingFaceModelProvider)


def test_factory_creates_azure_openai_provider():
    model = SimpleNamespace(
        provider=ModelProvider.AZURE_OPENAI,
    )

    with (
        patch(
            "app.services.model_gateway.factory.settings.azure_openai_api_key",
            "test-azure-key",
        ),
        patch(
            "app.services.model_gateway.factory.settings.azure_openai_endpoint",
            "https://test.openai.azure.com/",
        ),
        patch(
            "app.services.model_gateway.factory.settings.azure_openai_api_version",
            "2024-10-21",
        ),
    ):
        gateway = ModelGatewayFactory.create(model)

    assert isinstance(gateway, AzureOpenAIModelProvider)
