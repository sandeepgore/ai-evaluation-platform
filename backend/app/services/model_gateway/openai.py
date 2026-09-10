import time
from typing import Any

from openai import AsyncOpenAI

from app.schemas.model_gateway import ModelResponse
from app.services.model_gateway.base import ModelGateway


class OpenAIModelProvider(ModelGateway):
    """OpenAI model gateway."""

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, *, api_key: str | None):
        if not api_key:
            raise ValueError("OpenAI API key is not configured")

        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        configuration = configuration or {}

        model = configuration.get("model", self.DEFAULT_MODEL)

        start_time = time.perf_counter()

        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        output = ""
        if response.choices:
            output = response.choices[0].message.content or ""

        usage = response.usage

        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        return ModelResponse(
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            trace={
                "provider": "openai",
                "model": model,
            },
        )
