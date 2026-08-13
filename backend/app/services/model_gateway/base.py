import asyncio
from abc import ABC, abstractmethod
from typing import Any

from app.schemas.model_gateway import ModelResponse
from app.schemas.model_gateway.batch_response import BatchModelResponse


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
    ) -> list[BatchModelResponse]:
        """
        Generate responses for multiple prompts concurrently.

        Each prompt is isolated independently.

        A failure for one prompt does not fail the entire batch.
        """
        if not prompts:
            return []

        configuration = configuration or {}

        async def generate_one(
            index: int,
            prompt: str,
        ) -> BatchModelResponse:
            try:
                response = await self.generate(
                    prompt=prompt,
                    configuration=configuration,
                )

                return BatchModelResponse(
                    index=index,
                    response=response,
                    error=None,
                )

            except Exception as exc:
                return BatchModelResponse(
                    index=index,
                    response=None,
                    error={
                        "type": type(exc).__name__,
                        "message": str(exc) or repr(exc),
                    },
                )

        return list(
            await asyncio.gather(
                *(generate_one(index, prompt) for index, prompt in enumerate(prompts))
            )
        )
