from app.config.settings import settings
from app.models.model import Model, ModelProvider
from app.services.model_gateway.base import ModelGateway
from app.services.model_gateway.mock import MockModelProvider
from app.services.model_gateway.ollama import OllamaModelProvider
from app.services.model_gateway.openai import OpenAIModelProvider
from app.services.model_gateway.anthropic import AnthropicModelProvider
from app.services.model_gateway.google import GoogleModelProvider
from app.services.model_gateway.huggingface import HuggingFaceModelProvider
from app.services.model_gateway.azure_openai import AzureOpenAIModelProvider


class ModelGatewayFactory:
    @staticmethod
    def create(model: Model) -> ModelGateway:
        if model.provider == ModelProvider.MOCK:
            return MockModelProvider()

        if model.provider == ModelProvider.OLLAMA:
            return OllamaModelProvider()

        if model.provider == ModelProvider.OPENAI:
            return OpenAIModelProvider(
                api_key=settings.openai_api_key,
            )

        if model.provider == ModelProvider.ANTHROPIC:
            return AnthropicModelProvider(
                api_key=settings.anthropic_api_key,
            )

        if model.provider == ModelProvider.GOOGLE:
            return GoogleModelProvider(
                api_key=settings.google_api_key,
            )

        if model.provider == ModelProvider.HUGGINGFACE:
            return HuggingFaceModelProvider(
                api_key=settings.huggingface_api_key,
            )

        if model.provider == ModelProvider.AZURE_OPENAI:
            return AzureOpenAIModelProvider(
                api_key=settings.azure_openai_api_key,
                endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )

        if model.provider == ModelProvider.CUSTOM:
            raise ValueError("Custom model providers are not supported yet.")

        raise ValueError(f"Unsupported model provider: {model.provider}")
