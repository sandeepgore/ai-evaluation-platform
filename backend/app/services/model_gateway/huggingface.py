import time
from typing import Any

from huggingface_hub import AsyncInferenceClient
from openai import AsyncOpenAI

from app.config.settings import settings
from app.schemas.model_gateway import ModelResponse
from app.services.model_gateway.base import ModelGateway
from app.services.model_gateway.execution import ModelExecutionMode


class HuggingFaceModelProvider(ModelGateway):
    def __init__(
        self,
        *,
        api_key: str | None = None,
    ) -> None:
        self.api_key = api_key

    async def generate(
        self,
        *,
        prompt: str,
        configuration: dict[str, Any] | None = None,
    ) -> ModelResponse:
        configuration = configuration or {}

        model = configuration.get("model")
        if not model:
            raise ValueError("Hugging Face model identifier is required.")

        mode = configuration.get(
            "mode",
            ModelExecutionMode.HOSTED.value,
        )

        try:
            execution_mode = ModelExecutionMode(mode)
        except ValueError as exc:
            raise ValueError(f"Unsupported Hugging Face execution mode: {mode}") from exc

        if execution_mode == ModelExecutionMode.HOSTED:
            return await self._generate_hosted(
                prompt=prompt,
                model=model,
                configuration=configuration,
            )

        if execution_mode == ModelExecutionMode.LOCAL:
            return await self._generate_local(
                prompt=prompt,
                model=model,
                configuration=configuration,
            )

        if execution_mode == ModelExecutionMode.ENDPOINT:
            return await self._generate_endpoint(
                prompt=prompt,
                model=model,
                configuration=configuration,
            )

        raise ValueError(f"Unsupported Hugging Face execution mode: {mode}")

    async def _generate_hosted(
        self,
        *,
        prompt: str,
        model: str,
        configuration: dict[str, Any],
    ) -> ModelResponse:
        provider = configuration.get(
            "provider",
            "hf-inference",
        )

        timeout = configuration.get(
            "timeout",
            settings.model_gateway_timeout,
        )

        request_kwargs = self._build_request_kwargs(
            prompt=prompt,
            model=model,
            configuration=configuration,
        )

        client = AsyncInferenceClient(
            model=model,
            provider=provider,
            api_key=self.api_key,
            timeout=timeout,
        )

        start_time = time.perf_counter()

        try:
            response = await client.chat.completions.create(
                **request_kwargs,
            )
        except Exception as exc:
            raise RuntimeError(
                self._build_model_error(
                    mode=ModelExecutionMode.HOSTED.value,
                    model=model,
                    error=exc,
                )
            ) from exc

        latency_ms = (time.perf_counter() - start_time) * 1000

        return self._build_response(
            response=response,
            latency_ms=latency_ms,
            model=model,
            execution_mode=ModelExecutionMode.HOSTED.value,
            inference_provider=provider,
        )

    async def _generate_local(
        self,
        *,
        prompt: str,
        model: str,
        configuration: dict[str, Any],
    ) -> ModelResponse:
        base_url = configuration.get("base_url")

        if not base_url:
            raise ValueError("Hugging Face local execution requires 'base_url'.")

        timeout = configuration.get(
            "timeout",
            settings.model_gateway_timeout,
        )

        client = AsyncOpenAI(
            api_key="local",
            base_url=base_url,
            timeout=timeout,
        )

        request_kwargs = self._build_request_kwargs(
            prompt=prompt,
            model=model,
            configuration=configuration,
        )

        start_time = time.perf_counter()

        try:
            response = await client.chat.completions.create(
                **request_kwargs,
            )
        except Exception as exc:
            raise RuntimeError(
                self._build_model_error(
                    mode=ModelExecutionMode.LOCAL.value,
                    model=model,
                    error=exc,
                    base_url=base_url,
                )
            ) from exc

        latency_ms = (time.perf_counter() - start_time) * 1000

        return self._build_response(
            response=response,
            latency_ms=latency_ms,
            model=model,
            execution_mode=ModelExecutionMode.LOCAL.value,
        )

    async def _generate_endpoint(
        self,
        *,
        prompt: str,
        model: str,
        configuration: dict[str, Any],
    ) -> ModelResponse:
        base_url = configuration.get("base_url")

        if not base_url:
            raise ValueError("Hugging Face endpoint execution requires 'base_url'.")

        timeout = configuration.get(
            "timeout",
            settings.model_gateway_timeout,
        )

        provider = configuration.get(
            "provider",
            "hf-inference",
        )

        client = AsyncInferenceClient(
            model=model,
            provider=provider,
            api_key=self.api_key,
            base_url=base_url,
            timeout=timeout,
        )

        request_kwargs = self._build_request_kwargs(
            prompt=prompt,
            model=model,
            configuration=configuration,
        )

        start_time = time.perf_counter()

        try:
            response = await client.chat.completions.create(
                **request_kwargs,
            )
        except Exception as exc:
            raise RuntimeError(
                self._build_model_error(
                    mode=ModelExecutionMode.ENDPOINT.value,
                    model=model,
                    error=exc,
                    base_url=base_url,
                )
            ) from exc

        latency_ms = (time.perf_counter() - start_time) * 1000

        return self._build_response(
            response=response,
            latency_ms=latency_ms,
            model=model,
            execution_mode=ModelExecutionMode.ENDPOINT.value,
            inference_provider=provider,
        )

    @staticmethod
    def _build_request_kwargs(
        *,
        prompt: str,
        model: str,
        configuration: dict[str, Any],
    ) -> dict[str, Any]:
        request_kwargs: dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "model": model,
            "stream": False,
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

        return request_kwargs

    @staticmethod
    def _build_response(
        *,
        response: Any,
        latency_ms: float,
        model: str,
        execution_mode: str,
        inference_provider: str | None = None,
    ) -> ModelResponse:
        output = ""

        if response.choices:
            output = response.choices[0].message.content or ""

        usage = getattr(response, "usage", None)

        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0

        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        trace = {
            "provider": "huggingface",
            "model": model,
            "execution_mode": execution_mode,
        }

        if inference_provider:
            trace["inference_provider"] = inference_provider

        return ModelResponse(
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            trace=trace,
        )

    @staticmethod
    def _build_model_error(
        *,
        mode: str,
        model: str,
        error: Exception,
        base_url: str | None = None,
    ) -> str:
        message = str(error).strip() or repr(error)

        location = f" at {base_url}" if base_url else ""

        return (
            f"Hugging Face model '{model}' could not be invoked "
            f"using {mode} execution{location}. "
            f"Reason: {message}. "
            "Please verify that the model is available and the "
            "configured endpoint is reachable."
        )
