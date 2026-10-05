from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.evaluation.evaluation_run import EvaluationRunMode
from app.services.evaluation.dataset_capability import DatasetCapabilities
from app.services.evaluation.dataset_capability_service import (
    DatasetCapabilityService,
)
from app.services.evaluation.evaluation_data_requirements import (
    DataRequirement,
    EvaluationDataRequirementEvaluator,
)
from app.services.evaluators import Evaluator, EvaluatorRegistry
from app.services.evaluators.applicability import (
    EvaluationCapabilities,
    EvaluatorApplicabilityService,
)
from app.services.prompt.config import PromptConfig
from app.shared.enums import DataPolicy


class EvaluationRunValidationError(ValueError):
    """Raised when an evaluation run configuration violates
    platform validation rules.
    """

    def __init__(
        self,
        detail: str | dict[str, Any],
    ) -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True)
class DataPolicyConfiguration:
    policy: DataPolicy
    threshold: float


class EvaluationRunValidationService:
    """Validates an evaluation run before it is created or executed.

    Responsibilities:
    - Validate mode-specific configuration.
    - Resolve data policy configuration.
    - Read persisted dataset capabilities.
    - Resolve configured evaluators.
    - Validate evaluator applicability.
    - Validate evaluator data requirements against the selected policy.

    This service does not create or modify EvaluationRun records.
    """

    def __init__(
        self,
        evaluator_registry: EvaluatorRegistry,
    ) -> None:
        self.applicability_service = EvaluatorApplicabilityService(
            evaluator_registry,
        )

    # ------------------------------------------------------------------
    # Mode configuration
    # ------------------------------------------------------------------

    @staticmethod
    def validate_mode_configuration(
        *,
        mode: EvaluationRunMode,
        configuration: dict[str, Any],
    ) -> None:
        advanced_fields = {
            "evaluators",
            "execution_mode",
            "batch_size",
            "judge_model_id",
        }

        if mode == EvaluationRunMode.DEFAULT:
            configured_advanced_fields = sorted(
                advanced_fields.intersection(configuration),
            )

            if configured_advanced_fields:
                fields = ", ".join(configured_advanced_fields)

                raise EvaluationRunValidationError(
                    f"Default evaluation mode does not allow advanced configuration: {fields}."
                )

            return

        if mode == EvaluationRunMode.ADVANCED:
            evaluators = configuration.get("evaluators")

            if not evaluators:
                raise EvaluationRunValidationError(
                    "Advanced evaluation mode requires at least one evaluator."
                )

    # ------------------------------------------------------------------
    # Data policy
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_data_policy(
        configuration: dict[str, Any] | None,
    ) -> DataPolicyConfiguration:
        configuration = configuration or {}

        configured_policy = configuration.get(
            "data_policy",
        )

        if configured_policy is None:
            return DataPolicyConfiguration(
                policy=settings.default_data_policy,
                threshold=settings.default_data_policy_threshold,
            )

        if not isinstance(
            configured_policy,
            dict,
        ):
            raise EvaluationRunValidationError("'data_policy' must be an object.")

        policy_value = configured_policy.get(
            "type",
            settings.default_data_policy.value,
        )

        if not isinstance(
            policy_value,
            str,
        ):
            raise EvaluationRunValidationError("'data_policy.type' must be a string.")

        try:
            policy = DataPolicy(
                policy_value.lower(),
            )
        except ValueError as exc:
            raise EvaluationRunValidationError(
                f"Unsupported data policy '{policy_value}'. "
                "Supported policies are: strict, partial, threshold."
            ) from exc

        threshold = configured_policy.get(
            "threshold",
            settings.default_data_policy_threshold,
        )

        if not isinstance(
            threshold,
            (int, float),
        ) or isinstance(
            threshold,
            bool,
        ):
            raise EvaluationRunValidationError("'data_policy.threshold' must be a number.")

        threshold = float(threshold)

        if not 0.0 <= threshold <= 1.0:
            raise EvaluationRunValidationError(
                "'data_policy.threshold' must be between 0.0 and 1.0."
            )

        if policy != DataPolicy.THRESHOLD and "threshold" in configured_policy:
            raise EvaluationRunValidationError(
                "'data_policy.threshold' can only be configured "
                "when data policy type is 'threshold'."
            )

        return DataPolicyConfiguration(
            policy=policy,
            threshold=threshold,
        )

    # ------------------------------------------------------------------
    # Prompt configuration
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_prompt_config(
        configuration: dict[str, Any] | None,
    ) -> PromptConfig | None:
        configuration = configuration or {}

        configured_prompt = configuration.get(
            "prompt",
        )

        if configured_prompt is None:
            return None

        if not isinstance(
            configured_prompt,
            dict,
        ):
            raise EvaluationRunValidationError("'prompt' must be an object.")

        try:
            return PromptConfig.model_validate(
                configured_prompt,
            )
        except ValueError as exc:
            raise EvaluationRunValidationError(
                str(exc),
            ) from exc

    # ------------------------------------------------------------------
    # Evaluation capabilities
    # ------------------------------------------------------------------

    @staticmethod
    def build_capabilities(
        *,
        evaluation_type: str,
        dataset_capabilities: DatasetCapabilities,
    ) -> EvaluationCapabilities:
        available_inputs = {"actual_output"}

        if dataset_capabilities.has_reference:
            available_inputs.add(
                "expected_output",
            )

        if dataset_capabilities.has_context:
            available_inputs.add(
                "context",
            )

        return EvaluationCapabilities(
            evaluation_type=evaluation_type,
            has_reference=dataset_capabilities.has_reference,
            has_context=dataset_capabilities.has_context,
            available_inputs=frozenset(available_inputs),
        )

    # ------------------------------------------------------------------
    # Evaluator resolution
    # ------------------------------------------------------------------

    def resolve_evaluators(
        self,
        *,
        evaluation_type: str,
        mode: EvaluationRunMode,
        configuration: dict[str, Any],
        capabilities: EvaluationCapabilities,
        dataset_capabilities: DatasetCapabilities,
        policy: DataPolicy,
        threshold: float,
    ) -> list[Evaluator]:
        if mode == EvaluationRunMode.ADVANCED:
            try:
                return self.applicability_service.validate_configuration(
                    configuration,
                    capabilities,
                    defer_data_requirements=True,
                )
            except ValueError as exc:
                raise EvaluationRunValidationError(
                    str(exc),
                ) from exc

        from app.services.evaluation.evaluation_defaults import (
            DefaultEvaluationResolver,
        )

        evaluator_names = DefaultEvaluationResolver.resolve(
            evaluation_type,
            dataset_capabilities,
            policy=policy,
            threshold=threshold,
        )

        if not evaluator_names:
            raise EvaluationRunValidationError(
                "No evaluators are available for this evaluation configuration and dataset."
            )

        try:
            return self.applicability_service.validate(
                evaluator_names,
                capabilities,
                defer_data_requirements=True,
            )
        except ValueError as exc:
            raise EvaluationRunValidationError(
                str(exc),
            ) from exc

    # ------------------------------------------------------------------
    # Data requirements
    # ------------------------------------------------------------------

    @staticmethod
    def get_requirements(
        evaluators: list[Evaluator],
    ) -> set[DataRequirement]:
        requirements: set[DataRequirement] = set()

        for evaluator in evaluators:
            metadata = evaluator.metadata

            if metadata.requires_reference:
                requirements.add(
                    DataRequirement.REFERENCE,
                )

            if metadata.requires_context:
                requirements.add(
                    DataRequirement.CONTEXT,
                )

        return requirements

    # ------------------------------------------------------------------
    # Policy validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_policy(
        *,
        dataset_capabilities: DatasetCapabilities,
        requirements: set[DataRequirement],
        policy: DataPolicy,
        threshold: float,
    ) -> None:
        for requirement in sorted(
            requirements,
            key=lambda item: item.value,
        ):
            result = EvaluationDataRequirementEvaluator.evaluate(
                dataset_capabilities,
                requirement,
                policy,
                threshold=threshold,
            )

            decision = result.decision

            if decision.allowed:
                continue

            raise EvaluationRunValidationError(
                {
                    "message": ("Evaluation run violates the configured data policy."),
                    "policy": policy.value,
                    "requirement": requirement.value,
                    "coverage": decision.coverage,
                    "required_coverage": decision.required_coverage,
                    "reason": decision.reason,
                }
            )

    # ------------------------------------------------------------------
    # Full validation
    # ------------------------------------------------------------------

    async def validate(
        self,
        *,
        db: AsyncSession,
        dataset_version_id: UUID,
        evaluation_type: str,
        mode: EvaluationRunMode,
        configuration: dict[str, Any],
    ) -> None:
        # --------------------------------------------------------------
        # Mode configuration
        # --------------------------------------------------------------

        self.validate_mode_configuration(
            mode=mode,
            configuration=configuration,
        )

        # --------------------------------------------------------------
        # Dataset capabilities
        # --------------------------------------------------------------

        dataset_capabilities = await DatasetCapabilityService.analyze_dataset_version(
            db,
            dataset_version_id,
        )

        # --------------------------------------------------------------
        # Data policy
        # --------------------------------------------------------------

        policy_configuration = self.resolve_data_policy(
            configuration,
        )

        # --------------------------------------------------------------
        # Prompt configuration
        # --------------------------------------------------------------

        self.resolve_prompt_config(
            configuration,
        )

        # --------------------------------------------------------------
        # Evaluation capabilities
        # --------------------------------------------------------------

        capabilities = self.build_capabilities(
            evaluation_type=evaluation_type,
            dataset_capabilities=dataset_capabilities,
        )

        # --------------------------------------------------------------
        # Evaluators
        # --------------------------------------------------------------

        evaluators = self.resolve_evaluators(
            evaluation_type=evaluation_type,
            mode=mode,
            configuration=configuration,
            capabilities=capabilities,
            dataset_capabilities=dataset_capabilities,
            policy=policy_configuration.policy,
            threshold=policy_configuration.threshold,
        )

        # --------------------------------------------------------------
        # Data requirements
        # --------------------------------------------------------------

        requirements = self.get_requirements(
            evaluators,
        )

        # --------------------------------------------------------------
        # Data policy
        # --------------------------------------------------------------

        self.validate_policy(
            dataset_capabilities=dataset_capabilities,
            requirements=requirements,
            policy=policy_configuration.policy,
            threshold=policy_configuration.threshold,
        )
