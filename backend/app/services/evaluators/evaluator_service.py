from app.services.evaluators.base import Evaluator
from app.services.evaluators.registry import create_default_registry


class EvaluatorService:
    """
    Service for discovering and querying registered evaluators.

    The service uses the default evaluator registry as the single
    source of truth for available evaluators.
    """

    def __init__(self) -> None:
        self.registry = create_default_registry()

    def _get_unique_evaluators(self) -> list[Evaluator]:
        """
        Return canonical evaluators without registry aliases.

        Example:
            rouge_l
            rouge -> rouge_l

        The catalog exposes only rouge_l once.
        """

        evaluators: list[Evaluator] = []
        seen_names: set[str] = set()

        for name in self.registry.list_names():
            evaluator = self.registry.get(name)

            if evaluator.name in seen_names:
                continue

            seen_names.add(evaluator.name)
            evaluators.append(evaluator)

        return evaluators

    def list(
        self,
        *,
        category: str | None = None,
        requires_reference: bool | None = None,
        requires_context: bool | None = None,
        requires_llm: bool | None = None,
        applicable_to: str | None = None,
        tag: str | None = None,
    ) -> list[Evaluator]:
        """
        List registered evaluators using optional metadata filters.
        """

        evaluators = self._get_unique_evaluators()

        results: list[Evaluator] = []

        for evaluator in evaluators:
            metadata = evaluator.metadata

            if category is not None and metadata.category != category:
                continue

            if requires_reference is not None and metadata.requires_reference != requires_reference:
                continue

            if requires_context is not None and metadata.requires_context != requires_context:
                continue

            if requires_llm is not None and metadata.requires_llm != requires_llm:
                continue

            if applicable_to is not None and applicable_to not in metadata.applicable_to:
                continue

            if tag is not None and tag not in metadata.tags:
                continue

            results.append(evaluator)

        return results

    def get(self, name: str) -> Evaluator:
        """
        Get an evaluator by canonical name or registered alias.
        """

        return self.registry.get(name)
