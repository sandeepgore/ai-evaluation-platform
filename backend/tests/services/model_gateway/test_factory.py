from types import SimpleNamespace

import pytest

from app.models.model import ModelProvider
from app.services.model_gateway.factory import ModelGatewayFactory
from app.services.model_gateway.mock import MockModelProvider
from app.services.model_gateway.ollama import OllamaModelProvider


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


@pytest.mark.parametrize(
    "provider",
    [
        ModelProvider.OPENAI,
        ModelProvider.ANTHROPIC,
        ModelProvider.GOOGLE,
        ModelProvider.HUGGINGFACE,
        ModelProvider.AZURE_OPENAI,
        ModelProvider.CUSTOM,
    ],
)
def test_factory_rejects_unimplemented_provider(provider):
    model = SimpleNamespace(
        provider=provider,
    )

    with pytest.raises(ValueError):
        ModelGatewayFactory.create(model)
