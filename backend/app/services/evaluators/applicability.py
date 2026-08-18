from dataclasses import dataclass
from typing import Any

from app.services.evaluators.base import Evaluator
from app.services.evaluators.registry import EvaluatorRegistry


@dataclass(frozen=True)
class EvaluationCapabilities:
    """
    Capabilities available to an evaluation.

    These capabilities describe the inputs/resources available to the
    selected evaluators.
    """

    evaluation_type: str = "text"
    has_reference: bool = False
    has_context: bool = False
    llm_available: bool = False


class EvaluatorApplicabilityService:
    """
    Validates whether evaluators can be used for a given evaluation.

    The evaluator registry remains the single source of truth for
    evaluator metadata.
    """

    def __init__(self, registry: EvaluatorRegistry) -> None:
        self.registry = registry

    def is_applicable(
        self,
        evaluator: Evaluator,
        capabilities: EvaluationCapabilities,
    ) -> tuple[bool, str | None]:
        """
        Check whether one evaluator is applicable.

        Returns:
            (True, None) when applicable.
            (False, reason) when not applicable.
        """

        metadata = evaluator.metadata

        # --------------------------------------------------------------
        # Evaluation type
        # --------------------------------------------------------------

        if metadata.applicable_to and capabilities.evaluation_type not in metadata.applicable_to:
            return (
                False,
                (
                    f"Evaluator '{evaluator.name}' is not applicable to "
                    f"evaluation type '{capabilities.evaluation_type}'. "
                    f"Supported types: {list(metadata.applicable_to)}."
                ),
            )

        # --------------------------------------------------------------
        # Reference requirement
        # --------------------------------------------------------------

        if metadata.requires_reference and not capabilities.has_reference:
            return (
                False,
                (
                    f"Evaluator '{evaluator.name}' requires a reference "
                    "answer, but no reference is available."
                ),
            )

        # --------------------------------------------------------------
        # Context requirement
        # --------------------------------------------------------------

        if metadata.requires_context and not capabilities.has_context:
            return (
                False,
                (
                    f"Evaluator '{evaluator.name}' requires evaluation "
                    "context, but no context is available."
                ),
            )

        # --------------------------------------------------------------
        # LLM requirement
        # --------------------------------------------------------------

        if metadata.requires_llm and not capabilities.llm_available:
            return (
                False,
                (f"Evaluator '{evaluator.name}' requires an LLM, but no LLM is available."),
            )

        return True, None

    def validate(
        self,
        evaluator_names: list[str],
        capabilities: EvaluationCapabilities,
    ) -> list[Evaluator]:
        """
        Validate and resolve evaluator names.

        Supports canonical evaluator names and registry aliases.

        Raises:
            ValueError: If an evaluator is unknown, duplicated, or
            incompatible with the supplied evaluation capabilities.
        """

        if not evaluator_names:
            raise ValueError("At least one evaluator must be selected.")

        resolved: list[Evaluator] = []
        seen_names: set[str] = set()

        for name in evaluator_names:
            # ----------------------------------------------------------
            # Resolve evaluator through the registry.
            #
            # EvaluatorRegistry.get() raises ValueError for unknown
            # evaluators, so explicitly handle that contract here.
            # ----------------------------------------------------------

            try:
                evaluator = self.registry.get(name)
            except ValueError as exc:
                raise ValueError(f"Unknown evaluator: '{name}'.") from exc

            canonical_name = evaluator.name

            # ----------------------------------------------------------
            # Prevent duplicate evaluators.
            #
            # This also catches aliases pointing to the same evaluator.
            #
            # Example:
            #   rouge
            #   rouge_l
            #
            # Both resolve to canonical name "rouge_l".
            # ----------------------------------------------------------

            if canonical_name in seen_names:
                raise ValueError(f"Evaluator '{canonical_name}' was selected more than once.")

            # ----------------------------------------------------------
            # Validate evaluator applicability.
            # ----------------------------------------------------------

            applicable, reason = self.is_applicable(
                evaluator,
                capabilities,
            )

            if not applicable:
                raise ValueError(reason)

            seen_names.add(canonical_name)
            resolved.append(evaluator)

        return resolved

    def validate_configuration(
        self,
        configuration: dict[str, Any],
        capabilities: EvaluationCapabilities,
    ) -> list[Evaluator]:
        """
        Validate the evaluator section of an evaluation configuration.

        Supported configuration formats:

            "evaluators": [
                "exact_match",
                "f1"
            ]

        or:

            "evaluators": [
                {"name": "exact_match", "weight": 0.5},
                {"name": "f1", "weight": 0.5}
            ]
        """

        evaluator_configurations = configuration.get("evaluators")

        if not evaluator_configurations:
            raise ValueError("Evaluation configuration must contain at least one evaluator.")

        evaluator_names: list[str] = []

        for evaluator_configuration in evaluator_configurations:
            # ----------------------------------------------------------
            # Simple evaluator name
            # ----------------------------------------------------------

            if isinstance(evaluator_configuration, str):
                evaluator_names.append(evaluator_configuration)
                continue

            # ----------------------------------------------------------
            # Weighted evaluator configuration
            # ----------------------------------------------------------

            if isinstance(evaluator_configuration, dict):
                name = evaluator_configuration.get("name")

                if not isinstance(name, str) or not name.strip():
                    raise ValueError(
                        "Each evaluator configuration must contain a non-empty 'name'."
                    )

                evaluator_names.append(name)
                continue

            # ----------------------------------------------------------
            # Invalid evaluator configuration
            # ----------------------------------------------------------

            raise ValueError(
                "Each evaluator must be either a string or an object containing a 'name'."
            )

        return self.validate(
            evaluator_names,
            capabilities,
        )
