from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class JudgeConfiguration:
    """
    Configuration for an LLM-based evaluator judge.

    The judge model is intentionally independent from the model
    being evaluated.
    """

    enabled: bool = True

    provider: str = "ollama"

    model: str = "llama3.2:3b"

    base_url: str | None = None

    timeout: float = 60.0

    criteria: str = (
        "Evaluate the quality of the actual output against the "
        "expected output. Consider correctness, relevance, and "
        "completeness."
    )

    min_score: float = 0.0

    max_score: float = 1.0

    temperature: float | None = None

    extra_configuration: dict[str, Any] = field(default_factory=dict)

    def to_model_configuration(self) -> dict[str, Any]:
        """
        Convert judge configuration into ModelGateway configuration.
        """

        configuration: dict[str, Any] = {
            "model": self.model,
            "timeout": self.timeout,
        }

        if self.base_url is not None:
            configuration["base_url"] = self.base_url

        if self.temperature is not None:
            configuration["temperature"] = self.temperature

        configuration.update(self.extra_configuration)

        return configuration
