import asyncio
import time
from typing import Any

import httpx

from app.schemas.model_gateway.response import ModelResponse
from app.schemas.model_gateway.batch_response import BatchModelResponse
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

        # Preserve httpx exceptions.
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

    async def generate_batch(
        self,
        *,
        prompts: list[str],
        configuration: dict[str, Any] | None = None,
    ) -> list[ModelResponse]:
        """
        Generate multiple Ollama responses with bounded concurrency.

        Each prompt is executed independently.

        A failure for one prompt does not fail the other prompts.
        Failed prompts are returned as exceptions so the evaluation
        engine can isolate failed cases.
        """

        if not prompts:
            return []

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

        concurrency = int(
            configuration.get(
                "batch_concurrency",
                2,
            )
        )

        if concurrency <= 0:
            raise ValueError("'batch_concurrency' must be greater than zero.")

        semaphore = asyncio.Semaphore(concurrency)

        async with httpx.AsyncClient(timeout=timeout) as client:

            async def generate_one(
                index: int,
                prompt: str,
            ) -> BatchModelResponse:
                async with semaphore:
                    try:
                        # TEMPORARY FAILURE-INJECTION TEST
                        if "capital of France" in prompt:
                            raise RuntimeError(
                                "INTENTIONAL TEST FAILURE - Ollama batch failure isolation"
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

                        model_response = ModelResponse(
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

                        return BatchModelResponse(
                            index=index,
                            response=model_response,
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

            results = await asyncio.gather(
                *(generate_one(index, prompt) for index, prompt in enumerate(prompts))
            )

        # Important:
        # Do NOT raise the first exception here.
        #
        # The evaluation engine needs to know which individual
        # case failed so it can isolate that case.
        return list(results)
