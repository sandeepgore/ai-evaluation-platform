import time
from typing import Any

from google import genai

from app.schemas.model_gateway import ModelResponse
from app.services.model_gateway.base import ModelGateway


class GoogleModelProvider(ModelGateway):
    """Google Gemini model gateway."""

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, *, api_key: str | None):
        if not api_key:
            raise ValueError("Google API key is not configured")

        self.client = genai.Client(api_key=api_key)

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        configuration = configuration or {}

        model = configuration.get("model", self.DEFAULT_MODEL)

        start_time = time.perf_counter()

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        output = response.text or ""

        usage = response.usage_metadata

        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0
        total_tokens = usage.total_token_count if usage else 0

        return ModelResponse(
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            trace={
                "provider": "google",
                "model": model,
            },
        )
