import pytest

from app.services.evaluators.base import EvaluationScore, Evaluator
from app.services.evaluators.registry import (
    EvaluatorRegistry,
    create_default_registry,
)


class FakeEvaluator(Evaluator):
    def __init__(self, evaluator_name: str) -> None:
        self._name = evaluator_name

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict | None = None,
    ) -> EvaluationScore:
        return EvaluationScore(
            metric=self.name,
            score=1.0,
            feedback="Fake evaluation completed.",
        )


def test_registry_registers_evaluator():
    registry = EvaluatorRegistry()
    evaluator = FakeEvaluator("custom")

    registry.register(evaluator)

    assert registry.get("custom") is evaluator
    assert registry.list_names() == ["custom"]


def test_registry_raises_value_error_for_unknown_evaluator():
    registry = EvaluatorRegistry()

    with pytest.raises(
        ValueError,
        match="Unknown evaluator: unknown",
    ):
        registry.get("unknown")


def test_registry_get_many_returns_registered_evaluators():
    registry = EvaluatorRegistry()

    exact_match = FakeEvaluator("exact_match")
    f1 = FakeEvaluator("f1")

    registry.register(exact_match)
    registry.register(f1)

    evaluators = registry.get_many(
        [
            "exact_match",
            "f1",
        ]
    )

    assert evaluators == [
        exact_match,
        f1,
    ]


def test_registry_get_many_ignores_unknown_names():
    registry = EvaluatorRegistry()

    exact_match = FakeEvaluator("exact_match")

    registry.register(exact_match)

    evaluators = registry.get_many(
        [
            "exact_match",
            "unknown",
        ]
    )

    assert evaluators == [exact_match]


def test_registry_register_alias():
    registry = EvaluatorRegistry()

    rouge = FakeEvaluator("rouge_l")

    registry.register(rouge)
    registry.register_alias("rouge", rouge)

    assert registry.get("rouge_l") is rouge
    assert registry.get("rouge") is rouge


def test_registry_alias_can_be_used_in_get_many():
    registry = EvaluatorRegistry()

    rouge = FakeEvaluator("rouge_l")

    registry.register(rouge)
    registry.register_alias("rouge", rouge)

    evaluators = registry.get_many(
        [
            "rouge",
        ]
    )

    assert evaluators == [rouge]


def test_default_registry_contains_all_current_evaluators():
    registry = create_default_registry()

    expected_names = {
        "exact_match",
        "contains",
        "f1",
        "bleu",
        "rouge_l",
        "rouge",
        "relevance",
        "faithfulness",
    }

    assert set(registry.list_names()) == expected_names


@pytest.mark.parametrize(
    "name",
    [
        "exact_match",
        "contains",
        "f1",
        "bleu",
        "rouge_l",
        "rouge",
        "relevance",
        "faithfulness",
    ],
)
def test_default_registry_returns_evaluator(name: str):
    registry = create_default_registry()

    evaluator = registry.get(name)

    assert evaluator is not None
    assert isinstance(evaluator, Evaluator)
