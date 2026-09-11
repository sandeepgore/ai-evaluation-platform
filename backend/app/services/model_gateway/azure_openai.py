import time
from typing import Any

from openai import AsyncAzureOpenAI

from app.config.settings import settings
from app.schemas.model_gateway import ModelResponse
from app.services.model_gateway.base import ModelGateway


class AzureOpenAIModelProvider(ModelGateway):
    """Azure OpenAI model gateway."""

    def __init__(
        self,
        *,
        api_key: str | None,
        endpoint: str | None,
        api_version: str | None,
    ) -> None:
        if not api_key:
            raise ValueError("Azure OpenAI API key is not configured")

        if not endpoint:
            raise ValueError("Azure OpenAI endpoint is not configured")

        self.api_key = api_key
        self.endpoint = endpoint
        self.default_api_version = api_version

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        configuration = configuration or {}

        model = configuration.get("model")

        if not model:
            raise ValueError("Azure OpenAI deployment name is required.")

        api_version = configuration.get(
            "api_version",
            self.default_api_version,
        )

        if not api_version:
            raise ValueError("Azure OpenAI API version is required.")

        timeout = configuration.get(
            "timeout",
            settings.model_gateway_timeout,
        )

        client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=api_version,
            timeout=timeout,
        )

        request_kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        temperature = configuration.get("temperature")
        if temperature is not None:
            request_kwargs["temperature"] = temperature

        max_tokens = configuration.get("max_tokens")
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        response_format = configuration.get("response_format")

        if response_format is not None:
            if response_format != "json":
                raise ValueError("Only 'json' response format is supported.")

            request_kwargs["response_format"] = {
                "type": "json_object",
            }

        start_time = time.perf_counter()

        try:
            response = await client.chat.completions.create(
                **request_kwargs,
            )
        except Exception as exc:
            message = str(exc).strip() or repr(exc)

            raise RuntimeError(
                f"Azure OpenAI deployment '{model}' could not be "
                f"invoked. Reason: {message}. "
                "Please verify that the deployment exists, the "
                "endpoint is reachable, and the configured "
                "credentials and API version are valid."
            ) from exc

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
                "provider": "azure_openai",
                "model": model,
                "api_version": api_version,
            },
        )
