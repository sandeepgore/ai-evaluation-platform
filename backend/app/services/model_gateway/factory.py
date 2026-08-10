from app.models.model import Model, ModelProvider
from app.services.model_gateway.base import ModelGateway
from app.services.model_gateway.mock import MockModelProvider


class ModelGatewayFactory:
    """
    Creates the appropriate ModelGateway implementation
    for a configured model.
    """

    @staticmethod
    def create(model: Model) -> ModelGateway:
        if model.provider == ModelProvider.MOCK:
            return MockModelProvider()

        if model.provider == ModelProvider.OLLAMA:
            raise ValueError("Ollama model provider is not implemented yet.")

        if model.provider == ModelProvider.OPENAI:
            raise ValueError("OpenAI model provider is not implemented yet.")

        if model.provider == ModelProvider.ANTHROPIC:
            raise ValueError("Anthropic model provider is not implemented yet.")

        if model.provider == ModelProvider.GOOGLE:
            raise ValueError("Google model provider is not implemented yet.")

        if model.provider == ModelProvider.HUGGINGFACE:
            raise ValueError("Hugging Face model provider is not implemented yet.")

        if model.provider == ModelProvider.AZURE_OPENAI:
            raise ValueError("Azure OpenAI model provider is not implemented yet.")

        if model.provider == ModelProvider.CUSTOM:
            raise ValueError("Custom model providers are not supported yet.")

        raise ValueError(f"Unsupported model provider: {model.provider}")
