import time
from typing import Any

from app.schemas.model_gateway import ModelResponse
from app.services.model_gateway.base import ModelGateway


class MockModelProvider(ModelGateway):
    """
    Mock model provider used for local development and testing.

    This provider does not call an external LLM.
    It generates deterministic responses so that the
    evaluation pipeline can be tested end-to-end.
    """

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        start_time = time.perf_counter()

        configuration = configuration or {}

        response_prefix = configuration.get(
            "response_prefix",
            "Mock response:",
        )

        output = f"{response_prefix} {prompt}"

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        input_tokens = len(prompt.split())
        output_tokens = len(output.split())

        return ModelResponse(
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=elapsed_ms,
            trace={
                "provider": "mock",
                "model": configuration.get(
                    "model",
                    "mock-model-v1",
                ),
            },
        )

    async def generate_batch(
        self,
        *,
        prompts: list[str],
        configuration: dict[str, Any] | None = None,
    ) -> list[ModelResponse]:
        """
        Generate responses for multiple prompts concurrently.

        The mock provider uses the base concurrency semantics while
        preserving the input order.
        """

        return await super().generate_batch(
            prompts=prompts,
            configuration=configuration,
        )
