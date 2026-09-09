from dataclasses import dataclass
from typing import Any

from app.services.evaluators.base import Evaluator
from app.services.evaluators.registry import EvaluatorRegistry


@dataclass(frozen=True)
class EvaluationCapabilities:
    """Capabilities available to an evaluation.

    These capabilities describe the inputs/resources available to the
    selected evaluators.

    High-level capabilities such as `has_reference` and `has_context`
    are translated into evaluator inputs by the applicability service.
    """

    evaluation_type: str = "text"

    has_reference: bool = False
    has_context: bool = False
    llm_available: bool = False

    # Optional explicit inputs for future/custom evaluator requirements.
    available_inputs: frozenset[str] = frozenset()


class EvaluatorApplicabilityService:
    """Validates whether evaluators can be used for a given evaluation.

    The evaluator registry remains the single source of truth for
    evaluator metadata.

    Data requirements can optionally be deferred for evaluation-run
    validation. When deferred, dataset-level reference/context
    availability is not treated as an evaluator configuration error.
    The authoritative data policy and case-level eligibility layers
    remain responsible for deciding whether those requirements can
    actually be satisfied.
    """

    def __init__(self, registry: EvaluatorRegistry) -> None:
        self.registry = registry

    def _get_available_inputs(
        self,
        capabilities: EvaluationCapabilities,
    ) -> set[str]:
        """Resolve the concrete evaluator inputs available from the high-level evaluation
        capabilities.

        The evaluation engine always provides `actual_output`.

        `expected_output` is available when the dataset contains
        reference answers.

        `context` is available when the dataset contains evaluation
        context.

        Explicit `available_inputs` can be used for future/custom
        evaluator inputs.
        """

        available_inputs = set(capabilities.available_inputs)

        # Every evaluator evaluates a model-generated output.
        available_inputs.add("actual_output")

        if capabilities.has_reference:
            available_inputs.add("expected_output")

        if capabilities.has_context:
            available_inputs.add("context")

        return available_inputs

    def is_applicable(
        self,
        evaluator: Evaluator,
        capabilities: EvaluationCapabilities,
        *,
        defer_data_requirements: bool = False,
    ) -> tuple[bool, str | None]:
        """Determine whether an evaluator is applicable to the supplied evaluation
        capabilities.

        Args:
            evaluator: Evaluator being validated.

            capabilities: Dataset/evaluation capabilities available to the
              run.

            defer_data_requirements: When False, all evaluator data
              requirements are validated immediately.

                When True, dataset-derived reference/context requirements
                are deferred to the data-policy and case-eligibility
                layers. Other requirements, such as evaluation type,
                LLM availability, and custom evaluator inputs, remain
                strict.

        Returns:
            (True, None) when applicable.

            (False, reason) when the evaluator cannot safely be used.
        """

        metadata = evaluator.metadata

        # --------------------------------------------------------------
        # 1. Validate evaluation type.
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
        # 2. Validate high-level resource requirements.
        #
        # Reference/context requirements may be deferred because their
        # final decision belongs to the data-policy + case-eligibility
        # layers.
        #
        # LLM availability remains strict because an evaluator requiring
        # an LLM cannot operate without one.
        # --------------------------------------------------------------

        if not defer_data_requirements:
            if metadata.requires_reference and not capabilities.has_reference:
                return (
                    False,
                    (
                        f"Evaluator '{evaluator.name}' requires a reference "
                        "answer, but no reference is available."
                    ),
                )

            if metadata.requires_context and not capabilities.has_context:
                return (
                    False,
                    (
                        f"Evaluator '{evaluator.name}' requires evaluation "
                        "context, but no context is available."
                    ),
                )

        if metadata.requires_llm and not capabilities.llm_available:
            return (
                False,
                f"Evaluator '{evaluator.name}' requires an LLM, but no LLM is available.",
            )

        # --------------------------------------------------------------
        # 3. Resolve concrete evaluator inputs.
        # --------------------------------------------------------------

        available_inputs = self._get_available_inputs(
            capabilities,
        )

        required_inputs = set(
            metadata.required_inputs,
        )

        # When reference/context requirements are deferred, ignore the
        # concrete inputs automatically derived from those requirements.
        #
        # Only these dataset-derived inputs are deferred:
        #   requires_reference -> expected_output
        #   requires_context   -> context
        #
        # Other custom evaluator inputs remain strict.
        if defer_data_requirements:
            if metadata.requires_reference:
                required_inputs.discard(
                    "expected_output",
                )

            if metadata.requires_context:
                required_inputs.discard(
                    "context",
                )

        missing_inputs = required_inputs - available_inputs

        if missing_inputs:
            return (
                False,
                (
                    f"Evaluator '{evaluator.name}' requires inputs "
                    f"{sorted(missing_inputs)}, but they are not available."
                ),
            )

        return True, None

    def get_applicable_evaluators(
        self,
        capabilities: EvaluationCapabilities,
    ) -> list[Evaluator]:
        """Return all evaluators applicable to the supplied capabilities.

        Evaluators are returned using their canonical names.

        Registry aliases are automatically deduplicated.

        The evaluator registry remains the single source of truth for
        evaluator discovery.

        This method intentionally uses strict applicability because
        discovery should represent evaluators that are immediately
        usable with the supplied capabilities.
        """

        applicable_evaluators: list[Evaluator] = []
        seen_names: set[str] = set()

        for name in self.registry.list_names():
            evaluator = self.registry.get(name)

            canonical_name = evaluator.name

            if canonical_name in seen_names:
                continue

            applicable, _ = self.is_applicable(
                evaluator,
                capabilities,
            )

            if not applicable:
                continue

            seen_names.add(canonical_name)
            applicable_evaluators.append(evaluator)

        return applicable_evaluators

    def validate(
        self,
        evaluator_names: list[str],
        capabilities: EvaluationCapabilities,
        *,
        defer_data_requirements: bool = False,
    ) -> list[Evaluator]:
        """Validate and resolve evaluator names.

        Supports canonical evaluator names and registry aliases.

        Args:
            evaluator_names: Evaluators selected for the evaluation.

            capabilities: Dataset/evaluation capabilities available to the run.

            defer_data_requirements: When True, dataset-derived reference/context
              requirements are deferred to the data-policy and
              case-eligibility layers.

        Raises:
            ValueError: If an evaluator is unknown, duplicated, or incompatible
              with the supplied evaluation capabilities.
        """

        if not evaluator_names:
            raise ValueError("At least one evaluator must be selected.")

        resolved: list[Evaluator] = []
        seen_names: set[str] = set()

        for name in evaluator_names:
            try:
                evaluator = self.registry.get(name)
            except ValueError as exc:
                raise ValueError(f"Unknown evaluator: '{name}'.") from exc

            canonical_name = evaluator.name

            if canonical_name in seen_names:
                raise ValueError(f"Evaluator '{canonical_name}' was selected more than once.")

            applicable, reason = self.is_applicable(
                evaluator,
                capabilities,
                defer_data_requirements=defer_data_requirements,
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
        *,
        defer_data_requirements: bool = False,
    ) -> list[Evaluator]:
        """Validate the evaluator section of an evaluation configuration.

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

        When `defer_data_requirements=True`, reference/context
        requirements are intentionally deferred to the run-level
        data-policy and case-level eligibility layers.
        """

        evaluator_configurations = configuration.get(
            "evaluators",
        )

        if not evaluator_configurations:
            raise ValueError("Evaluation configuration must contain at least one evaluator.")

        evaluator_names: list[str] = []

        for evaluator_configuration in evaluator_configurations:
            if isinstance(evaluator_configuration, str):
                evaluator_names.append(
                    evaluator_configuration,
                )
                continue

            if isinstance(evaluator_configuration, dict):
                name = evaluator_configuration.get(
                    "name",
                )

                if not isinstance(name, str) or not name.strip():
                    raise ValueError(
                        "Each evaluator configuration must contain a non-empty 'name'."
                    )

                evaluator_names.append(
                    name,
                )
                continue

            raise ValueError(
                "Each evaluator must be either a string or an object containing a 'name'."
            )

        return self.validate(
            evaluator_names,
            capabilities,
            defer_data_requirements=defer_data_requirements,
        )
