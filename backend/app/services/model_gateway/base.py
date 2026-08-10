import asyncio
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
        """
        raise NotImplementedError

    async def generate_batch(
        self,
        *,
        prompts: list[str],
        configuration: dict[str, Any] | None = None,
    ) -> list[ModelResponse]:
        """
        Generate responses for multiple prompts.

        The default implementation executes requests concurrently.
        Provider implementations can override this when the provider
        exposes a native batch API.
        """

        if not prompts:
            return []

        responses = await asyncio.gather(
            *(
                self.generate(
                    prompt=prompt,
                    configuration=configuration,
                )
                for prompt in prompts
            )
        )

        return list(responses)
