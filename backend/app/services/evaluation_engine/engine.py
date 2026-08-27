from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.model import Model
from app.schemas.model_gateway.batch_response import BatchModelResponse
from app.schemas.model_gateway.response import ModelResponse
from app.services.dataset_case import DatasetCaseService
from app.services.evaluation import EvaluationRunService
from app.services.evaluation.dataset_capability import (
    DatasetCapabilityAnalyzer,
)
from app.services.evaluation_engine.feedback import (
    EvaluationRunFeedbackService,
)
from app.services.evaluation_engine.scoring_config import (
    ScoringConfigurationService,
)
from app.services.evaluation_results import EvaluationResultService
from app.services.evaluators import Evaluator, EvaluatorRegistry
from app.services.evaluators.applicability import (
    EvaluationCapabilities,
    EvaluatorApplicabilityService,
)
from app.services.evaluators.llm_judge import LLMJudgeEvaluator
from app.services.model_gateway import (
    ModelGateway,
    ModelGatewayFactory,
)
from app.services.scoring import ScoringService


class EvaluationEngine:
    """
    Orchestrates the execution of an EvaluationRun.

    Supports two execution modes:

    sequential:
        Case
          -> model.generate()
          -> evaluate
          -> score
          -> save

    batch:
        Batch
          -> model.generate_batch()
          -> evaluate each response
          -> score
          -> save each result

    Evaluators remain sequential within each case.

    Additional responsibilities:

    - Resolve evaluator applicability.
    - Resolve dedicated LLM judge configuration.
    - Resolve scoring configuration.
    - Generate deterministic run-level feedback.
    - Maintain run lifecycle state and timing.
    """

    def __init__(
        self,
        db: AsyncSession,
        model_gateway: ModelGateway | None,
        evaluator_registry: EvaluatorRegistry,
        scoring_service: ScoringService,
        applicability_service: EvaluatorApplicabilityService | None = None,
        scoring_configuration_service: ScoringConfigurationService | None = None,
        feedback_service: EvaluationRunFeedbackService | None = None,
    ) -> None:
        self.db = db
        self.model_gateway = model_gateway
        self.evaluator_registry = evaluator_registry

        self.applicability_service = applicability_service or EvaluatorApplicabilityService(
            evaluator_registry
        )

        self.scoring_service = scoring_service

        self.scoring_configuration_service = (
            scoring_configuration_service or ScoringConfigurationService()
        )

        self.feedback_service = feedback_service or EvaluationRunFeedbackService()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _validate_llm_available_configuration(
        self,
        run: EvaluationRun,
    ) -> None:
        """
        Validate the optional llm_available configuration field.

        llm_available is a configuration capability declaration and,
        when explicitly supplied, must be a boolean.

        The actual evaluator LLM availability is determined by resolving
        the dedicated judge model gateway.
        """

        configuration = run.configuration or {}

        if "llm_available" not in configuration:
            return

        llm_available = configuration["llm_available"]

        if not isinstance(
            llm_available,
            bool,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'llm_available' must be a boolean.",
            )

    def _get_evaluation_capabilities(
        self,
        *,
        run: EvaluationRun,
        cases: list[Any],
        llm_available: bool = False,
    ) -> EvaluationCapabilities:
        """
        Determine the capabilities available to the evaluation run.

        Dataset capabilities are delegated to DatasetCapabilityAnalyzer.

        A capability is considered available for evaluator applicability
        only when every case in the evaluation dataset provides it.

        The evaluator LLM remains separate from the model being evaluated.
        """

        evaluation_type = run.evaluation_type.value

        dataset_capabilities = DatasetCapabilityAnalyzer.analyze(cases)

        has_reference = dataset_capabilities.all_cases_have_reference
        has_context = dataset_capabilities.all_cases_have_context

        available_inputs: set[str] = {
            "actual_output",
        }

        if has_reference:
            available_inputs.add("expected_output")

        if has_context:
            available_inputs.add("context")

        if not isinstance(
            llm_available,
            bool,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'llm_available' must be a boolean.",
            )

        return EvaluationCapabilities(
            evaluation_type=evaluation_type,
            has_reference=has_reference,
            has_context=has_context,
            llm_available=llm_available,
            available_inputs=frozenset(available_inputs),
        )

    def _get_default_evaluator_names(
        self,
        evaluation_type: str,
    ) -> list[str]:
        """
        Return the default evaluators for an evaluation type.

        Explicit evaluator configuration always takes precedence.
        """

        defaults = {
            "text": [
                "exact_match",
                "contains",
                "f1",
                "bleu",
                "rouge_l",
            ],
            "rag": [
                "relevance",
                "faithfulness",
                "f1",
            ],
        }

        return defaults.get(
            evaluation_type,
            ["exact_match"],
        )

    def _get_evaluators(
        self,
        run: EvaluationRun,
        capabilities: EvaluationCapabilities,
    ) -> list[tuple[Evaluator, float]]:
        """
        Resolve and validate evaluators configured for the evaluation run.

        Evaluator metadata and applicability rules are delegated to
        EvaluatorApplicabilityService.

        The returned evaluator list preserves the configured order
        and evaluator weights.
        """

        evaluation_type = run.evaluation_type.value

        evaluator_config: list[str | dict[str, Any]] = self._get_default_evaluator_names(
            evaluation_type
        )

        if run.configuration:
            configured_evaluators = run.configuration.get("evaluators")

            if configured_evaluators:
                evaluator_config = configured_evaluators

        if not isinstance(
            evaluator_config,
            list,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'evaluators' must be a list.",
            )

        if not evaluator_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one evaluator must be configured.",
            )

        parsed_configurations: list[tuple[str, float]] = []

        for item in evaluator_config:
            if isinstance(item, str):
                evaluator_name = item
                weight = 1.0

            elif isinstance(item, dict):
                evaluator_name = item.get("name")
                weight = item.get("weight", 1.0)

                if not isinstance(
                    evaluator_name,
                    str,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=("Each evaluator configuration must contain a string 'name'."),
                    )

                if not isinstance(
                    weight,
                    (int, float),
                ) or isinstance(
                    weight,
                    bool,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(f"Weight for evaluator '{evaluator_name}' must be a number."),
                    )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Each evaluator must be either a string "
                        "or an object containing 'name' and 'weight'."
                    ),
                )

            evaluator_name = evaluator_name.strip()

            if not evaluator_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Evaluator name must not be empty.",
                )

            if weight <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(f"Weight for evaluator '{evaluator_name}' must be greater than zero."),
                )

            parsed_configurations.append(
                (
                    evaluator_name,
                    float(weight),
                )
            )

        evaluator_names = [evaluator_name for evaluator_name, _weight in parsed_configurations]

        try:
            validated_evaluators = self.applicability_service.validate(
                evaluator_names,
                capabilities,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        if len(validated_evaluators) != len(parsed_configurations):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evaluator validation returned an unexpected result.",
            )

        evaluators: list[tuple[Evaluator, float]] = []

        for evaluator, (
            _configured_name,
            weight,
        ) in zip(
            validated_evaluators,
            parsed_configurations,
            strict=True,
        ):
            evaluators.append(
                (
                    evaluator,
                    weight,
                )
            )

        return evaluators

    def _get_execution_mode(
        self,
        run: EvaluationRun,
    ) -> str:
        """
        Resolve the configured execution mode.

        Supported values:

            sequential
            batch

        Defaults to sequential.
        """

        execution_mode = "sequential"

        if run.configuration:
            configured_mode = run.configuration.get("execution_mode")

            if configured_mode is not None:
                if not isinstance(
                    configured_mode,
                    str,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="'execution_mode' must be a string.",
                    )

                execution_mode = configured_mode.lower()

        if execution_mode not in {
            "sequential",
            "batch",
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("'execution_mode' must be either 'sequential' or 'batch'."),
            )

        return execution_mode

    def _get_batch_size(
        self,
        run: EvaluationRun,
    ) -> int:
        """
        Resolve the configured batch size.

        Defaults to 10.
        """

        batch_size = 10

        if run.configuration:
            configured_batch_size = run.configuration.get("batch_size")

            if configured_batch_size is not None:
                if not isinstance(
                    configured_batch_size,
                    int,
                ) or isinstance(
                    configured_batch_size,
                    bool,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="'batch_size' must be an integer.",
                    )

                if configured_batch_size <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="'batch_size' must be greater than zero.",
                    )

                batch_size = configured_batch_size

        return batch_size

    # ------------------------------------------------------------------
    # Model configuration
    # ------------------------------------------------------------------

    async def _resolve_judge_model_gateway(
        self,
        run: EvaluationRun,
    ) -> tuple[ModelGateway, dict[str, Any]] | None:
        """
        Resolve the dedicated LLM judge model gateway.

        The judge model is configured using:

            configuration["judge_model_id"]

        Returns:
            ModelGateway and model configuration when a judge model
            is configured.

            None when no judge model is configured.

        Raises:
            HTTPException when the configured judge model is invalid,
            missing, inactive, or unsupported.
        """

        if not run.configuration:
            return None

        judge_model_id = run.configuration.get("judge_model_id")

        if judge_model_id is None:
            return None

        if not isinstance(
            judge_model_id,
            str,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'judge_model_id' must be a UUID string.",
            )

        try:
            judge_model_uuid = UUID(judge_model_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'judge_model_id' must be a valid UUID.",
            ) from exc

        judge_model_result = await self.db.execute(
            select(Model).where(
                Model.id == judge_model_uuid,
                Model.is_active.is_(True),
            )
        )

        judge_model = judge_model_result.scalar_one_or_none()

        if judge_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Judge model not found or inactive.",
            )

        try:
            return (
                ModelGatewayFactory.create(judge_model),
                judge_model.configuration or {},
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Judge model configuration is invalid: {exc}",
            ) from exc

    def _build_configuration(
        self,
        *,
        model: Model,
        run: EvaluationRun,
    ) -> dict[str, Any]:
        """
        Build the final configuration passed to the model gateway.

        Model configuration is loaded first and evaluation-run
        configuration overrides it.
        """

        configuration: dict[str, Any] = {}

        if model.configuration:
            configuration.update(model.configuration)

        if run.configuration:
            configuration.update(run.configuration)

        configuration.setdefault(
            "model",
            model.model_identifier,
        )

        return configuration

    # ------------------------------------------------------------------
    # Timing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_now() -> datetime:
        """
        Return the current timezone-aware UTC datetime.
        """

        return datetime.now(timezone.utc)

    @staticmethod
    def _calculate_duration_ms(
        started_at: datetime,
        completed_at: datetime,
    ) -> int:
        """
        Calculate execution duration in milliseconds.
        """

        return max(
            0,
            int((completed_at - started_at).total_seconds() * 1000),
        )

    # ------------------------------------------------------------------
    # Case evaluation
    # ------------------------------------------------------------------

    async def _evaluate_case(
        self,
        *,
        run: EvaluationRun,
        case: Any,
        response: Any,
        evaluator_configs: list[tuple[Evaluator, float]],
        scoring_configuration: dict[str, Any],
    ) -> None:
        """
        Evaluate and persist one successful model response.

        The scoring configuration is resolved once per evaluation run
        and reused for every case.
        """

        scores: dict[str, dict[str, Any]] = {}
        feedback_messages: list[str] = []

        for evaluator, _weight in evaluator_configs:
            evaluation_context: dict[str, Any] = {
                "input": case.input,
            }

            case_metadata = getattr(
                case,
                "case_metadata",
                None,
            )

            if case_metadata:
                evaluation_context.update(case_metadata)

            evaluation_score = await evaluator.evaluate(
                expected_output=case.expected_output,
                actual_output=response.output,
                context=evaluation_context,
            )

            scores[evaluation_score.metric] = {
                "score": evaluation_score.score,
                "metadata": evaluation_score.metadata,
            }

            if evaluation_score.feedback:
                feedback_messages.append(f"{evaluation_score.metric}: {evaluation_score.feedback}")

        # Use the run-level scoring configuration resolved by
        # ScoringConfigurationService.
        case_scoring_configuration = scoring_configuration.copy()

        # Evaluator weights come from the evaluator configuration
        # resolved for this run.
        case_scoring_configuration["weights"] = {
            evaluator.name: weight for evaluator, weight in evaluator_configs
        }

        scoring_result = self.scoring_service.calculate(
            scores=scores,
            configuration=case_scoring_configuration,
        )

        scores["overall"] = {
            "score": scoring_result.score,
            "metadata": scoring_result.metadata,
        }

        feedback = "\n".join(feedback_messages) if feedback_messages else None

        await EvaluationResultService.create(
            self.db,
            evaluation_run_id=run.id,
            dataset_case_id=case.id,
            status="completed",
            actual_output=response.output,
            expected_output=case.expected_output,
            scores=scores,
            feedback=feedback,
            trace=response.trace,
            latency_ms=int(response.latency_ms),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            error_message=None,
        )

        run.completed_cases += 1

    async def _save_failed_case(
        self,
        *,
        run: EvaluationRun,
        case: Any,
        exc: Exception,
    ) -> None:
        """
        Persist a failed evaluation case with a useful diagnostic message.
        """

        error_message = f"{type(exc).__name__}: {str(exc) or repr(exc)}"

        await EvaluationResultService.create(
            self.db,
            evaluation_run_id=run.id,
            dataset_case_id=case.id,
            status="failed",
            actual_output=None,
            expected_output=case.expected_output,
            scores={},
            feedback=None,
            trace={
                "error_type": type(exc).__name__,
            },
            latency_ms=None,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            error_message=error_message,
        )

        run.failed_cases += 1

    # ------------------------------------------------------------------
    # Sequential execution
    # ------------------------------------------------------------------

    async def _execute_sequential(
        self,
        *,
        run: EvaluationRun,
        cases: list[Any],
        model: Model,
        evaluator_configs: list[tuple[Evaluator, float]],
        model_gateway: ModelGateway,
        scoring_configuration: dict[str, Any],
    ) -> None:
        """
        Execute cases one at a time.

        Database changes are committed once after all cases have been
        processed instead of committing after every individual case.
        """

        configuration = self._build_configuration(
            model=model,
            run=run,
        )

        for case in cases:
            try:
                response = await model_gateway.generate(
                    prompt=case.input,
                    configuration=configuration,
                )

                await self._evaluate_case(
                    run=run,
                    case=case,
                    response=response,
                    evaluator_configs=evaluator_configs,
                    scoring_configuration=scoring_configuration,
                )

            except Exception as exc:
                await self._save_failed_case(
                    run=run,
                    case=case,
                    exc=exc,
                )

        await self.db.commit()

    # ------------------------------------------------------------------
    # Batch execution
    # ------------------------------------------------------------------

    async def _execute_batch(
        self,
        *,
        run: EvaluationRun,
        cases: list[Any],
        model: Model,
        evaluator_configs: list[tuple[Evaluator, float]],
        model_gateway: ModelGateway,
        batch_size: int,
        scoring_configuration: dict[str, Any],
    ) -> None:
        """
        Execute cases in batches.

        The model gateway may return either:

        - BatchModelResponse objects containing:
            index, response, error

        - raw ModelResponse objects for backward compatibility.

        Gateway-level exceptions fail the entire batch.

        Per-item errors only fail the corresponding case.

        Successful responses are evaluated and persisted normally.

        Execution continues with subsequent batches even when a batch
        or individual item fails.
        """

        configuration = self._build_configuration(
            model=model,
            run=run,
        )

        for start in range(
            0,
            len(cases),
            batch_size,
        ):
            batch_cases = cases[start : start + batch_size]

            prompts = [case.input for case in batch_cases]

            try:
                batch_results = await model_gateway.generate_batch(
                    prompts=prompts,
                    configuration=configuration,
                )

            except Exception as exc:
                for case in batch_cases:
                    await self._save_failed_case(
                        run=run,
                        case=case,
                        exc=exc,
                    )

                await self.db.commit()
                await self.db.refresh(run)

                continue

            if not isinstance(
                batch_results,
                list,
            ):
                batch_exc = RuntimeError("Model gateway returned an invalid batch response.")

                for case in batch_cases:
                    await self._save_failed_case(
                        run=run,
                        case=case,
                        exc=batch_exc,
                    )

                await self.db.commit()
                await self.db.refresh(run)

                continue

            if len(batch_results) != len(batch_cases):
                batch_exc = RuntimeError(
                    "Model gateway returned an unexpected number of responses."
                )

                for case in batch_cases:
                    await self._save_failed_case(
                        run=run,
                        case=case,
                        exc=batch_exc,
                    )

                await self.db.commit()
                await self.db.refresh(run)

                continue

            for case, result in zip(
                batch_cases,
                batch_results,
                strict=True,
            ):
                try:
                    if hasattr(result, "error") and hasattr(result, "response"):
                        if result.error is not None:
                            error_type = result.error.get(
                                "type",
                                "ModelGatewayError",
                            )

                            error_message = result.error.get(
                                "message",
                                "Unknown model gateway error.",
                            )

                            raise RuntimeError(f"{error_type}: {error_message}")

                        response = result.response

                        if response is None:
                            raise RuntimeError(
                                "Batch model gateway returned no response and no error."
                            )

                    else:
                        response = result

                    if response is None:
                        raise RuntimeError("Model gateway returned an empty response.")

                    await self._evaluate_case(
                        run=run,
                        case=case,
                        response=response,
                        evaluator_configs=evaluator_configs,
                        scoring_configuration=scoring_configuration,
                    )

                except Exception as exc:
                    await self._save_failed_case(
                        run=run,
                        case=case,
                        exc=exc,
                    )

            await self.db.commit()
            await self.db.refresh(run)

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------

    async def execute(
        self,
        run_id: UUID,
    ) -> EvaluationRun:
        """
        Execute all dataset cases belonging to an evaluation run.

        High-level lifecycle:

            PENDING
                |
                v
            validate configuration
                |
                v
            resolve model / evaluators / scoring configuration
                |
                v
            RUNNING
                |
                v
            execute cases
                |
                v
            generate run feedback
                |
                v
            COMPLETED / FAILED
        """

        # --------------------------------------------------------------
        # 1. Load evaluation run
        # --------------------------------------------------------------

        run = await EvaluationRunService.get_by_id(
            self.db,
            run_id,
        )

        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation run not found.",
            )

        # --------------------------------------------------------------
        # 2. Validate run state
        # --------------------------------------------------------------

        if run.status == EvaluationRunStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Evaluation run is already running.",
            )

        if run.status == EvaluationRunStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Evaluation run has already completed.",
            )

        if run.status == EvaluationRunStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Evaluation run has been cancelled.",
            )

        # --------------------------------------------------------------
        # 3. Validate run configuration
        #
        # Configuration validation must happen before:
        #
        #   - model lookup
        #   - model gateway resolution
        #   - judge gateway resolution
        #   - dataset execution
        #   - RUNNING state
        #
        # This guarantees invalid configuration is rejected before
        # inference begins.
        # --------------------------------------------------------------

        self._validate_llm_available_configuration(run)

        execution_mode = self._get_execution_mode(run)
        batch_size = self._get_batch_size(run)

        # --------------------------------------------------------------
        # 4. Validate associated model
        # --------------------------------------------------------------

        model_result = await self.db.execute(
            select(Model).where(
                Model.id == run.model_id,
                Model.is_active.is_(True),
            )
        )

        model = model_result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found or inactive.",
            )

        # --------------------------------------------------------------
        # 5. Resolve model gateway
        # --------------------------------------------------------------

        model_gateway = self.model_gateway

        if model_gateway is None:
            try:
                model_gateway = ModelGatewayFactory.create(model)

            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

        # --------------------------------------------------------------
        # 6. Resolve dedicated judge model gateway
        # --------------------------------------------------------------

        judge_model_resolution = await self._resolve_judge_model_gateway(run)

        judge_model_gateway = None
        judge_model_configuration: dict[str, Any] = {}

        if judge_model_resolution is not None:
            (
                judge_model_gateway,
                judge_model_configuration,
            ) = judge_model_resolution

        # --------------------------------------------------------------
        # 7. Bind dedicated judge model gateway
        #
        # llm_judge remains discoverable through the evaluator registry.
        #
        # The actual judge gateway is bound only when the evaluation
        # run resolves a valid dedicated judge model.
        # --------------------------------------------------------------

        if judge_model_gateway is not None:
            try:
                existing_judge = self.evaluator_registry.get("llm_judge")

                if isinstance(
                    existing_judge,
                    LLMJudgeEvaluator,
                ):
                    existing_judge.set_model_gateway(
                        judge_model_gateway,
                        judge_model_configuration,
                    )

                else:
                    # Allows lightweight/custom registries used by tests
                    # or integrations to provide their own llm_judge
                    # implementation.
                    self.evaluator_registry.register(
                        LLMJudgeEvaluator(
                            model_gateway=judge_model_gateway,
                            model_configuration=judge_model_configuration,
                        )
                    )

            except (ValueError, KeyError):
                try:
                    self.evaluator_registry.register(
                        LLMJudgeEvaluator(
                            model_gateway=judge_model_gateway,
                            model_configuration=judge_model_configuration,
                        )
                    )

                except Exception as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(f"Failed to register LLM judge evaluator: {exc}"),
                    ) from exc

            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(f"Failed to configure LLM judge evaluator: {exc}"),
                ) from exc

        # --------------------------------------------------------------
        # 8. Load dataset cases
        # --------------------------------------------------------------

        cases = await DatasetCaseService.list(
            self.db,
            run.dataset_version_id,
        )

        run.total_cases = len(cases)
        run.completed_cases = 0
        run.failed_cases = 0

        # --------------------------------------------------------------
        # 9. Determine evaluation capabilities
        # --------------------------------------------------------------

        evaluation_capabilities = self._get_evaluation_capabilities(
            run=run,
            cases=cases,
            llm_available=judge_model_gateway is not None,
        )

        # --------------------------------------------------------------
        # 10. Resolve and validate evaluators
        # --------------------------------------------------------------

        evaluator_configs = self._get_evaluators(
            run,
            evaluation_capabilities,
        )

        # --------------------------------------------------------------
        # 11. Resolve scoring configuration
        #
        # PostgreSQL is the source of truth.
        #
        # ScoringConfigurationService first checks Redis and falls back
        # to PostgreSQL when the cache is unavailable or misses.
        #
        # The resolved configuration is fetched once per run and then
        # reused for every evaluation case.
        # --------------------------------------------------------------

        scoring_configuration = await self.scoring_configuration_service.get(
            self.db,
            run.id,
        )

        # --------------------------------------------------------------
        # 12. Start evaluation timing
        # --------------------------------------------------------------

        started_at = self._utc_now()

        run.started_at = started_at
        run.completed_at = None
        run.duration_ms = None
        run.status = EvaluationRunStatus.RUNNING

        await self.db.commit()
        await self.db.refresh(run)

        # --------------------------------------------------------------
        # 13. Execute evaluation
        # --------------------------------------------------------------

        try:
            if execution_mode == "sequential":
                await self._execute_sequential(
                    run=run,
                    cases=cases,
                    model=model,
                    evaluator_configs=evaluator_configs,
                    model_gateway=model_gateway,
                    scoring_configuration=scoring_configuration,
                )

            elif execution_mode == "batch":
                await self._execute_batch(
                    run=run,
                    cases=cases,
                    model=model,
                    evaluator_configs=evaluator_configs,
                    model_gateway=model_gateway,
                    batch_size=batch_size,
                    scoring_configuration=scoring_configuration,
                )

            # ----------------------------------------------------------
            # 14. Generate deterministic run-level feedback
            #
            # Case-level results have already been committed by the
            # execution path, so the feedback service can safely query
            # EvaluationResult records.
            # ----------------------------------------------------------

            run.summary_feedback = await self.feedback_service.generate(
                self.db,
                run.id,
            )

            # ----------------------------------------------------------
            # 15. Complete evaluation run
            # ----------------------------------------------------------

            completed_at = self._utc_now()

            run.status = EvaluationRunStatus.COMPLETED
            run.completed_at = completed_at
            run.duration_ms = self._calculate_duration_ms(
                started_at,
                completed_at,
            )

            await self.db.commit()
            await self.db.refresh(run)

            return run

        except Exception:
            # ----------------------------------------------------------
            # 16. Unexpected engine-level failure
            #
            # Individual case failures are intentionally handled inside
            # the execution methods and do not reach this block.
            #
            # This block represents an unexpected engine-level failure.
            # ----------------------------------------------------------

            completed_at = self._utc_now()

            run.status = EvaluationRunStatus.FAILED
            run.completed_at = completed_at
            run.duration_ms = self._calculate_duration_ms(
                started_at,
                completed_at,
            )

            await self.db.commit()
            await self.db.refresh(run)

            raise
