from app.services.evaluators.base import Evaluator
from app.services.evaluators.bleu import BLEUEvaluator
from app.services.evaluators.contains import ContainsEvaluator
from app.services.evaluators.exact_match import ExactMatchEvaluator
from app.services.evaluators.f1 import F1Evaluator
from app.services.evaluators.faithfulness import FaithfulnessEvaluator
from app.services.evaluators.relevance import RelevanceEvaluator
from app.services.evaluators.rouge import ROUGELvaluator


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[str, Evaluator] = {}

    def register(self, evaluator: Evaluator) -> None:
        self._evaluators[evaluator.name] = evaluator

    def register_alias(self, alias: str, evaluator: Evaluator) -> None:
        self._evaluators[alias] = evaluator

    def get(self, name: str) -> Evaluator | None:
        return self._evaluators.get(name)

    def get_many(self, names: list[str]) -> list[Evaluator]:
        return [self._evaluators[name] for name in names if name in self._evaluators]

    def list_names(self) -> list[str]:
        return list(self._evaluators.keys())


def create_default_registry() -> EvaluatorRegistry:
    registry = EvaluatorRegistry()

    registry.register(ExactMatchEvaluator())
    registry.register(ContainsEvaluator())
    registry.register(F1Evaluator())
    registry.register(BLEUEvaluator())

    rouge_evaluator = ROUGELvaluator()
    registry.register(rouge_evaluator)
    registry.register_alias("rouge", rouge_evaluator)

    registry.register(RelevanceEvaluator())
    registry.register(FaithfulnessEvaluator())

    return registry
