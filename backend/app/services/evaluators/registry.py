from app.services.evaluators.base import Evaluator
from app.services.evaluators.contains import ContainsEvaluator
from app.services.evaluators.exact_match import ExactMatchEvaluator
from app.services.evaluators.f1 import F1Evaluator

class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[str, Evaluator] = {}

    def register(self, evaluator: Evaluator) -> None:
        self._evaluators[evaluator.name] = evaluator

    def get(self, name: str) -> Evaluator:
        evaluator = self._evaluators.get(name)

        if evaluator is None:
            raise ValueError(f"Unknown evaluator: {name}")

        return evaluator

    def list(self) -> list[str]:
        return list(self._evaluators.keys())


def create_default_registry() -> EvaluatorRegistry:
    registry = EvaluatorRegistry()

    registry.register(ExactMatchEvaluator())
    registry.register(ContainsEvaluator())
    registry.register(F1Evaluator())


    return registry

