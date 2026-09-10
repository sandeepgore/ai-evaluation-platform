import time
from typing import Any

from anthropic import AsyncAnthropic

from app.schemas.model_gateway import ModelResponse
from app.services.model_gateway.base import ModelGateway


class AnthropicModelProvider(ModelGateway):
    """Anthropic model gateway."""

    DEFAULT_MODEL = "claude-sonnet-4-5"

    def __init__(self, *, api_key: str | None):
        if not api_key:
            raise ValueError("Anthropic API key is not configured")

        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        configuration = configuration or {}

        model = configuration.get("model", self.DEFAULT_MODEL)
        max_tokens = configuration.get("max_tokens", 1024)

        start_time = time.perf_counter()

        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        output = ""
        if response.content:
            output = response.content[0].text or ""

        usage = response.usage

        input_tokens = usage.input_tokens if usage else 0
        output_tokens = usage.output_tokens if usage else 0
        total_tokens = input_tokens + output_tokens

        return ModelResponse(
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            trace={
                "provider": "anthropic",
                "model": model,
            },
        )
