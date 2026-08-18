from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvaluatorMetadata:
    """
    Static metadata describing an evaluator.

    Metadata is used for:
        - evaluator discovery
        - evaluator categorization
        - evaluator descriptions
        - required input declaration
        - applicability filtering
        - UI/API presentation
        - future evaluator configuration

    Metadata does not affect the evaluator's core evaluation logic.
    """

    category: str = "general"

    description: str = ""

    required_inputs: tuple[str, ...] = field(default_factory=tuple)

    requires_reference: bool = False
    requires_context: bool = False
    requires_llm: bool = False

    applicable_to: tuple[str, ...] = ("text",)

    tags: tuple[str, ...] = field(default_factory=tuple)


class EvaluationScore:
    """
    Standardized result returned by every evaluator.
    """

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
        """
        Convert the evaluation score into a serializable dictionary.
        """
        return {
            "metric": self.metric,
            "score": self.score,
            "feedback": self.feedback,
            "metadata": self.metadata,
        }


class Evaluator(ABC):
    """
    Base interface for all evaluators.

    Every evaluator must provide:
        - a unique name
        - evaluation logic

    Evaluators may optionally override `metadata` to describe:
        - category
        - description
        - required inputs
        - reference/context/LLM requirements
        - supported data types
        - tags
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique evaluator name.

        Example:
            "exact_match"
        """
        raise NotImplementedError

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing this evaluator.

        Individual evaluators can override this property when
        they need evaluator-specific metadata.

        The default metadata keeps existing evaluators backward
        compatible.
        """
        return EvaluatorMetadata()

    @abstractmethod
    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Evaluate a model output and return a standardized score.
        """
        raise NotImplementedError
