from abc import ABC, abstractmethod
from typing import Any


class ScoreCalculationResult:
    def __init__(
        self,
        *,
        score: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.score = score
        self.metadata = metadata or {}


class ScoreCalculator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique scoring strategy name."""
        raise NotImplementedError

    @abstractmethod
    def calculate(
        self,
        *,
        scores: dict[str, dict[str, Any]],
        configuration: dict[str, Any] | None = None,
    ) -> ScoreCalculationResult:
        """Calculate an aggregate score."""
        raise NotImplementedError