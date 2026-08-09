from abc import ABC, abstractmethod
from typing import Any

from app.schemas.model_gateway import ModelResponse


class ModelGateway(ABC):
    """
    Abstract interface for model providers.

    The evaluation engine depends on this interface rather than
    directly depending on a specific model provider.
    """

    @abstractmethod
    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """
        Generate a response from the configured model provider.

        Args:
            prompt: Input prompt sent to the model.
            configuration: Provider/model-specific configuration.

        Returns:
            A standardized ModelResponse.
        """
        raise NotImplementedError