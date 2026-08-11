import time
from typing import Any

import httpx

from app.schemas.model_gateway.response import ModelResponse
from app.services.model_gateway.base import ModelGateway


class OllamaModelProvider(ModelGateway):
    """
    Ollama model provider.

    Communicates with a locally running Ollama server
    through its HTTP API.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2:3b"
    DEFAULT_TIMEOUT = 60.0

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        configuration = configuration or {}

        base_url = configuration.get(
            "base_url",
            self.DEFAULT_BASE_URL,
        ).rstrip("/")

        model = configuration.get(
            "model",
            self.DEFAULT_MODEL,
        )

        timeout = float(
            configuration.get(
                "timeout",
                self.DEFAULT_TIMEOUT,
            )
        )

        started_at = time.perf_counter()

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        message = data.get("message", {})
        output = message.get("content", "")

        elapsed_ms = (time.perf_counter() - started_at) * 1000

        input_tokens = int(data.get("prompt_eval_count", 0))

        output_tokens = int(data.get("eval_count", 0))

        return ModelResponse(
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=elapsed_ms,
            trace={
                "provider": "ollama",
                "model": model,
                "base_url": base_url,
                "done_reason": data.get("done_reason"),
            },
        )
