from typing import Any

from app.services.evaluators.base import Evaluator
from app.services.evaluators.bleu import BLEUEvaluator
from app.services.evaluators.contains import ContainsEvaluator
from app.services.evaluators.exact_match import ExactMatchEvaluator
from app.services.evaluators.f1 import F1Evaluator
from app.services.evaluators.faithfulness import FaithfulnessEvaluator
from app.services.evaluators.relevance import RelevanceEvaluator
from app.services.evaluators.rouge import ROUGELvaluator


class EvaluatorRegistry:
    """
    Central registry for all available evaluators.

    The registry is responsible only for evaluator registration,
    lookup, aliases, and discovery.

    Evaluator metadata and applicability rules remain defined by
    each evaluator through Evaluator.metadata.
    """

    def __init__(self) -> None:
        self._evaluators: dict[str, Evaluator] = {}

    def register(
        self,
        evaluator: Evaluator,
    ) -> None:
        """
        Register an evaluator using its canonical name.

        Raises:
            ValueError:
                If the evaluator name is already registered.
        """
        name = evaluator.name

        if name in self._evaluators:
            raise ValueError(f"Evaluator '{name}' is already registered.")

        self._evaluators[name] = evaluator

    def register_alias(
        self,
        alias: str,
        evaluator: Evaluator,
    ) -> None:
        """
        Register an alternate name for an existing evaluator.

        Aliases point to the same evaluator instance.

        Example:
            rouge -> rouge_l
        """
        if alias in self._evaluators:
            raise ValueError(f"Evaluator name or alias '{alias}' is already registered.")

        self._evaluators[alias] = evaluator

    def get(
        self,
        name: str,
    ) -> Evaluator:
        """
        Get an evaluator by canonical name or alias.
        """
        evaluator = self._evaluators.get(name)

        if evaluator is None:
            raise ValueError(f"Unknown evaluator: {name}")

        return evaluator

    def get_many(
        self,
        names: list[str],
    ) -> list[Evaluator]:
        """
        Get multiple evaluators by name.

        Unknown evaluator names are ignored for backward compatibility.
        """
        return [self._evaluators[name] for name in names if name in self._evaluators]

    def list_names(self) -> list[str]:
        """
        Return all registered evaluator names and aliases.
        """
        return list(self._evaluators.keys())

    def list_evaluators(self) -> list[Evaluator]:
        """
        Return all registered evaluator instances.

        Aliases are excluded from discovery results.

        Example:
            rouge_l
            rouge

        Both point to the same ROUGELvaluator instance, so only
        the canonical evaluator is returned once.
        """
        evaluators: list[Evaluator] = []
        seen: set[int] = set()

        for evaluator in self._evaluators.values():
            evaluator_id = id(evaluator)

            if evaluator_id in seen:
                continue

            seen.add(evaluator_id)
            evaluators.append(evaluator)

        return evaluators

    def list_metadata(self) -> list[dict[str, Any]]:
        """
        Return metadata for all registered evaluators.

        Aliases are automatically deduplicated.

        The canonical evaluator name comes from Evaluator.name,
        while the remaining metadata comes from Evaluator.metadata.
        """
        metadata: list[dict[str, Any]] = []

        for evaluator in self.list_evaluators():
            evaluator_metadata = evaluator.metadata

            metadata.append(
                {
                    "name": evaluator.name,
                    "category": evaluator_metadata.category,
                    "description": evaluator_metadata.description,
                    "required_inputs": list(evaluator_metadata.required_inputs),
                    "requires_reference": evaluator_metadata.requires_reference,
                    "requires_context": evaluator_metadata.requires_context,
                    "requires_llm": evaluator_metadata.requires_llm,
                    "applicable_to": list(evaluator_metadata.applicable_to),
                    "tags": list(evaluator_metadata.tags),
                }
            )

        return metadata


def create_default_registry() -> EvaluatorRegistry:
    """
    Create the default evaluator registry.

    The registry is the single source of truth for evaluators
    available to the evaluation platform.
    """
    registry = EvaluatorRegistry()

    # --------------------------------------------------------------
    # General / correctness evaluators
    # --------------------------------------------------------------

    registry.register(ExactMatchEvaluator())

    registry.register(ContainsEvaluator())

    registry.register(F1Evaluator())

    # --------------------------------------------------------------
    # Similarity evaluators
    # --------------------------------------------------------------

    registry.register(BLEUEvaluator())

    rouge_evaluator = ROUGELvaluator()

    registry.register(rouge_evaluator)

    registry.register_alias(
        "rouge",
        rouge_evaluator,
    )

    # --------------------------------------------------------------
    # LLM / context-based evaluators
    # --------------------------------------------------------------

    registry.register(RelevanceEvaluator())

    registry.register(FaithfulnessEvaluator())

    return registry
