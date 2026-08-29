from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.model import Model
from app.schemas.model_gateway.batch_response import BatchModelResponse
from app.schemas.model_gateway.response import ModelResponse
from app.services.dataset_case import DatasetCaseService
from app.services.evaluation import EvaluationRunService
from app.services.evaluation.dataset_capability import (
    DatasetCapabilities,
    DatasetCapabilityAnalyzer,
)
from app.services.evaluation_engine.feedback_aggregation import (
    EvaluationFeedbackAggregationService,
)
from app.services.evaluation_engine.feedback_reducer import (
    EvaluationFeedbackReducer,
)
from app.services.evaluation_engine.scoring_config import (
    ScoringConfigurationService,
)
from app.services.evaluation_engine.summary import (
    EvaluationRunSummaryService,
)
from app.services.evaluation_engine.summary_persistence import (
    EvaluationSummaryPersistenceService,
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
from app.services.evaluation.evaluation_defaults import DefaultEvaluationResolver


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
    - Feed case-level evaluator feedback into the rolling reducer.
    - Generate deterministic run-level feedback.
    - Generate optional final LLM qualitative feedback.
    - Persist run summaries and cache them in Redis.
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
        redis: Redis | None = None,
        feedback_aggregation_service: (EvaluationFeedbackAggregationService | None) = None,
    ) -> None:
        self.db = db
        self.model_gateway = model_gateway
        self.evaluator_registry = evaluator_registry
        self.redis = redis

        self.applicability_service = applicability_service or EvaluatorApplicabilityService(
            evaluator_registry,
        )

        self.scoring_service = scoring_service

        self.scoring_configuration_service = (
            scoring_configuration_service or ScoringConfigurationService()
        )

        self.feedback_aggregation_service = feedback_aggregation_service

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

        Actual evaluator LLM availability is determined by resolving
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
        dataset_capabilities: DatasetCapabilities,
        llm_available: bool = False,
    ) -> EvaluationCapabilities:
        """
        Determine the capabilities available to the evaluation run.
        """

        evaluation_type = run.evaluation_type.value

        has_reference = dataset_capabilities.all_cases_have_reference
        has_context = dataset_capabilities.all_cases_have_context

        available_inputs: set[str] = {
            "actual_output",
        }

        if has_reference:
            available_inputs.add("expected_output")

        if has_context:
            available_inputs.add("context")

        if not isinstance(llm_available, bool):
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

    def _get_evaluators(
        self,
        run: EvaluationRun,
        capabilities: EvaluationCapabilities,
        dataset_capabilities: DatasetCapabilities,
    ) -> list[tuple[Evaluator, float]]:
        """
        Resolve and validate evaluators configured for the evaluation run.

        Evaluator metadata and applicability rules are delegated to
        EvaluatorApplicabilityService.

        The returned evaluator list preserves configured order and
        evaluator weights.
        """

        evaluation_type = run.evaluation_type.value

        evaluator_config: list[str | dict[str, Any]]

        if run.configuration:
            configured_evaluators = run.configuration.get(
                "evaluators",
            )
        else:
            configured_evaluators = None

        if configured_evaluators:
            evaluator_config = configured_evaluators
        else:
            evaluator_config = DefaultEvaluationResolver.resolve(
                evaluation_type,
                dataset_capabilities,
            )

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
                evaluator_name = item.get(
                    "name",
                )

                weight = item.get(
                    "weight",
                    1.0,
                )

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

        if len(validated_evaluators) != len(
            parsed_configurations,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Evaluator validation returned an unexpected result."),
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
            configured_mode = run.configuration.get(
                "execution_mode",
            )

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
            configured_batch_size = run.configuration.get(
                "batch_size",
            )

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
                        detail=("'batch_size' must be greater than zero."),
                    )

                batch_size = configured_batch_size

        return batch_size

    # ------------------------------------------------------------------
    # Model configuration
    # ------------------------------------------------------------------

    async def _resolve_judge_model_gateway(
        self,
        run: EvaluationRun,
    ) -> (
        tuple[
            ModelGateway,
            dict[str, Any],
            Model,
        ]
        | None
    ):
        """
        Resolve the dedicated LLM judge model gateway.

        The judge model is configured using:

            configuration["judge_model_id"]

        Returns the gateway, configuration, and Model when configured.

        Returns None when no judge model is configured.

        Raises HTTPException when the configured judge model is invalid,
        missing, inactive, or unsupported.
        """

        if not run.configuration:
            return None

        judge_model_id = run.configuration.get(
            "judge_model_id",
        )

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
            judge_model_uuid = UUID(
                judge_model_id,
            )
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
                ModelGatewayFactory.create(
                    judge_model,
                ),
                judge_model.configuration or {},
                judge_model,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"Judge model configuration is invalid: {exc}"),
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
            configuration.update(
                model.configuration,
            )

        if run.configuration:
            configuration.update(
                run.configuration,
            )

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

        return datetime.now(
            timezone.utc,
        )

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

        scores: dict[
            str,
            dict[str, Any],
        ] = {}

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
                evaluation_context.update(
                    case_metadata,
                )

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

        case_scoring_configuration = scoring_configuration.copy()

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

        evaluation_result = await EvaluationResultService.create(
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

        if self.feedback_aggregation_service is not None and evaluation_result.feedback:
            try:
                await self.feedback_aggregation_service.accept(
                    run.id,
                    evaluation_result.id,
                    evaluation_result.feedback,
                )
            except Exception:
                pass

        run.completed_cases += 1

    async def _save_failed_case(
        self,
        *,
        run: EvaluationRun,
        case: Any,
        exc: Exception,
    ) -> None:
        """
        Persist a failed evaluation case with a useful diagnostic
        message.
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

        Per-item errors are isolated to their corresponding case.

        Gateway-level exceptions fail every case in that batch.

        Execution continues with subsequent batches after failures.
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

            if len(batch_results) != len(
                batch_cases,
            ):
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
            finalize rolling feedback
                |
                v
            calculate persisted scores
                |
                v
            final LLM qualitative synthesis
                |
                v
            persist final summary
                |
                v
            cache final summary
                |
                v
            COMPLETED / FAILED
        """

        run = await EvaluationRunService.get_by_id(
            self.db,
            run_id,
        )

        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation run not found.",
            )

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

        self._validate_llm_available_configuration(
            run,
        )

        execution_mode = self._get_execution_mode(
            run,
        )

        batch_size = self._get_batch_size(
            run,
        )

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

        model_gateway = self.model_gateway

        if model_gateway is None:
            try:
                model_gateway = ModelGatewayFactory.create(
                    model,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

        judge_model_resolution = await self._resolve_judge_model_gateway(
            run,
        )

        judge_model_gateway = None
        judge_model_configuration: dict[str, Any] = {}
        resolved_judge_model: Model | None = None

        if judge_model_resolution is not None:
            (
                judge_model_gateway,
                judge_model_configuration,
                resolved_judge_model,
            ) = judge_model_resolution

        if judge_model_gateway is not None:
            try:
                existing_judge = self.evaluator_registry.get(
                    "llm_judge",
                )

                if isinstance(
                    existing_judge,
                    LLMJudgeEvaluator,
                ):
                    existing_judge.set_model_gateway(
                        judge_model_gateway,
                        judge_model_configuration,
                    )
                else:
                    self.evaluator_registry.register(
                        LLMJudgeEvaluator(
                            model_gateway=judge_model_gateway,
                            model_configuration=(judge_model_configuration),
                        )
                    )

            except (ValueError, KeyError):
                try:
                    self.evaluator_registry.register(
                        LLMJudgeEvaluator(
                            model_gateway=judge_model_gateway,
                            model_configuration=(judge_model_configuration),
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

        # Reuse the same resolved judge gateway for rolling feedback
        # reduction rather than resolving the judge model twice.
        #
        # An explicitly injected aggregation service is preserved.
        if (
            self.feedback_aggregation_service is None
            and self.redis is not None
            and judge_model_gateway is not None
            and resolved_judge_model is not None
        ):
            judge_provider = (
                resolved_judge_model.provider.value
                if hasattr(
                    resolved_judge_model.provider,
                    "value",
                )
                else str(
                    resolved_judge_model.provider,
                )
            )

            feedback_reducer = EvaluationFeedbackReducer(
                model_gateway=judge_model_gateway,
                model=resolved_judge_model.model_identifier,
                provider=judge_provider,
            )

            self.feedback_aggregation_service = EvaluationFeedbackAggregationService(
                redis=self.redis,
                reducer=feedback_reducer,
            )

        cases = await DatasetCaseService.list(
            self.db,
            run.dataset_version_id,
        )

        run.total_cases = len(cases)
        run.completed_cases = 0
        run.failed_cases = 0

        dataset_capabilities = DatasetCapabilityAnalyzer.analyze(
            cases,
        )

        evaluation_capabilities = self._get_evaluation_capabilities(
            run=run,
            dataset_capabilities=dataset_capabilities,
            llm_available=(judge_model_gateway is not None),
        )

        evaluator_configs = self._get_evaluators(
            run,
            evaluation_capabilities,
            dataset_capabilities,
        )

        scoring_configuration = await self.scoring_configuration_service.get(
            self.db,
            run.id,
        )

        started_at = self._utc_now()

        run.started_at = started_at
        run.completed_at = None
        run.duration_ms = None
        run.status = EvaluationRunStatus.RUNNING

        await self.db.commit()
        await self.db.refresh(run)

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

            # Rolling feedback is auxiliary qualitative processing.
            # Failure here must not invalidate completed case results.
            final_feedback = None

            if self.feedback_aggregation_service is not None:
                try:
                    finalization = await self.feedback_aggregation_service.finalize(
                        run.id,
                    )

                    if finalization.get(
                        "finalized",
                    ):
                        final_feedback = finalization.get(
                            "feedback",
                        )

                except Exception:
                    final_feedback = None

            # Finalize timing before summary calculation so the summary
            # contains the complete run duration.
            completed_at = self._utc_now()

            run.completed_at = completed_at
            run.duration_ms = self._calculate_duration_ms(
                started_at,
                completed_at,
            )

            # Calculate deterministic metrics exclusively from persisted
            # evaluation results. No final LLM calculation occurs here.
            summary = await EvaluationRunSummaryService.calculate(
                self.db,
                run.id,
            )

            # The final LLM is qualitative enrichment only. It receives
            # authoritative scores and performance data and does not
            # calculate or modify any metric.
            if judge_model_gateway is not None:
                try:
                    judge_model_name = (
                        resolved_judge_model.model_identifier
                        if resolved_judge_model is not None
                        else judge_model_configuration.get(
                            "model",
                            "llama3.2:3b",
                        )
                    )

                    judge_timeout = float(
                        judge_model_configuration.get(
                            "timeout",
                            60.0,
                        )
                    )

                    final_summary_feedback = (
                        await EvaluationRunSummaryService.generate_final_feedback(
                            model_gateway=judge_model_gateway,
                            evaluation_run_id=run.id,
                            overall_score=summary["overall_score"],
                            metrics=summary["metrics"],
                            performance=summary["performance"],
                            rolling_feedback=final_feedback,
                            model=judge_model_name,
                            timeout=judge_timeout,
                            base_url=(
                                judge_model_configuration.get(
                                    "base_url",
                                )
                            ),
                        )
                    )

                    summary["feedback"] = final_summary_feedback

                except Exception:
                    # The deterministic summary remains authoritative when
                    # final qualitative LLM synthesis fails.
                    summary["feedback"] = (
                        EvaluationRunSummaryService._build_final_fallback_feedback(
                            overall_score=summary["overall_score"],
                            metrics=summary["metrics"],
                            performance=summary["performance"],
                            completed_cases=summary["completed_cases"],
                            failed_cases=summary["failed_cases"],
                            rolling_feedback=final_feedback,
                        )
                    )

            else:
                summary["feedback"] = EvaluationRunSummaryService._build_final_fallback_feedback(
                    overall_score=summary["overall_score"],
                    metrics=summary["metrics"],
                    performance=summary["performance"],
                    completed_cases=summary["completed_cases"],
                    failed_cases=summary["failed_cases"],
                    rolling_feedback=final_feedback,
                )

            # PostgreSQL is the source of truth for the final summary.
            await EvaluationSummaryPersistenceService.save(
                self.db,
                run.id,
                summary,
            )

            # Redis is only a performance cache. Cache failures must not
            # invalidate an otherwise successfully persisted evaluation.
            if self.redis is not None:
                try:
                    from app.services.evaluation_engine.cache import (
                        EvaluationSummaryCache,
                    )

                    await EvaluationSummaryCache(
                        self.redis,
                    ).set(
                        run.id,
                        summary,
                    )
                except Exception:
                    pass

            # Reducer state is transient and can be removed only after
            # the final summary has been persisted.
            if self.feedback_aggregation_service is not None:
                try:
                    await self.feedback_aggregation_service.clear(
                        run.id,
                    )
                except Exception:
                    pass

            # Mark the run completed only after summary persistence has
            # succeeded.
            run.status = EvaluationRunStatus.COMPLETED

            await self.db.commit()
            await self.db.refresh(run)

            return run

        except Exception:
            # Individual case failures are isolated inside the execution
            # methods. This block handles unexpected engine-level failures.
            await self.db.rollback()

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
