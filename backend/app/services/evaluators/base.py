from abc import ABC, abstractmethod
from typing import Any


class EvaluationScore:
    def __init__(
        self,
        *,
        metric: str,
        score: float,
        feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.metric = metric
        self.score = score
        self.feedback = feedback
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "score": self.score,
            "feedback": self.feedback,
            "metadata": self.metadata,
        }


class Evaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique evaluator name."""
        raise NotImplementedError

    @abstractmethod
    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """Evaluate a model output."""
        raise NotImplementedError
