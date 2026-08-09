from typing import Any

from app.services.scoring.base import ScoreCalculator
from app.services.scoring.weighted import WeightedScoreCalculator


class ScoringService:
    def __init__(
        self,
        calculators: list[ScoreCalculator] | None = None,
    ) -> None:
        self._calculators: dict[str, ScoreCalculator] = {}

        for calculator in calculators or [
            WeightedScoreCalculator(),
        ]:
            self.register(calculator)

    def register(
        self,
        calculator: ScoreCalculator,
    ) -> None:
        self._calculators[calculator.name] = calculator

    def get(
        self,
        name: str,
    ) -> ScoreCalculator:
        calculator = self._calculators.get(name)

        if calculator is None:
            raise ValueError(
                f"Unknown scoring strategy: {name}"
            )

        return calculator

    def list(self) -> list[str]:
        return list(self._calculators.keys())

    def calculate(
        self,
        *,
        scores: dict[str, dict[str, Any]],
        configuration: dict[str, Any] | None = None,
        strategy: str = "weighted",
    ):
        calculator = self.get(strategy)

        return calculator.calculate(
            scores=scores,
            configuration=configuration,
        )