from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.model import Model
from app.services.dataset_case import DatasetCaseService
from app.services.evaluation import EvaluationRunService
from app.services.evaluation_results import EvaluationResultService
from app.services.evaluators import Evaluator, EvaluatorRegistry
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
        Case -> model.generate() -> evaluate -> score -> save

    batch:
        Batch -> model.generate_batch() -> evaluate each response
        -> score -> save each result

    Evaluators remain sequential within each case.
    """

    def __init__(
        self,
        db: AsyncSession,
        model_gateway: ModelGateway | None,
        evaluator_registry: EvaluatorRegistry,
        scoring_service: ScoringService,
    ) -> None:
        self.db = db
        self.model_gateway = model_gateway
        self.evaluator_registry = evaluator_registry
        self.scoring_service = scoring_service

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _get_evaluators(
        self,
        run: EvaluationRun,
    ) -> list[tuple[Evaluator, float]]:
        """
        Resolve evaluators configured for the evaluation run.

        Supported formats:

        Legacy:
        {
            "evaluators": [
                "exact_match",
                "contains"
            ]
        }

        Weighted:
        {
            "evaluators": [
                {
                    "name": "exact_match",
                    "weight": 0.5
                },
                {
                    "name": "contains",
                    "weight": 0.5
                }
            ]
        }

        Legacy evaluator names receive a default weight of 1.0.

        The evaluator weights are retained for compatibility.
        Score aggregation is delegated to ScoringService.
        """

        evaluator_config: Any = ["exact_match"]

        if run.configuration:
            configured_evaluators = run.configuration.get("evaluators")

            if configured_evaluators:
                evaluator_config = configured_evaluators

        if not isinstance(evaluator_config, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'evaluators' must be a list.",
            )

        evaluators: list[tuple[Evaluator, float]] = []
        evaluator_names: set[str] = set()

        for item in evaluator_config:
            if isinstance(item, str):
                evaluator_name = item
                weight = 1.0

            elif isinstance(item, dict):
                evaluator_name = item.get("name")
                weight = item.get("weight", 1.0)

                if not isinstance(evaluator_name, str):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=("Each evaluator configuration must contain a string 'name'."),
                    )

                if not isinstance(weight, (int, float)):
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

            if evaluator_name in evaluator_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(f"Evaluator '{evaluator_name}' is configured more than once."),
                )

            if weight <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(f"Weight for evaluator '{evaluator_name}' must be greater than zero."),
                )

            try:
                evaluator = self.evaluator_registry.get(evaluator_name)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

            evaluator_names.add(evaluator_name)
            evaluators.append((evaluator, float(weight)))

        if not evaluators:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one evaluator must be configured.",
            )

        return evaluators

    def _get_execution_mode(
        self,
        run: EvaluationRun,
    ) -> str:
        """
        Resolve the configured execution mode.

        Supported:

        {
            "execution_mode": "sequential"
        }

        {
            "execution_mode": "batch"
        }

        Defaults to sequential.
        """

        execution_mode = "sequential"

        if run.configuration:
            configured_mode = run.configuration.get("execution_mode")

            if configured_mode is not None:
                if not isinstance(configured_mode, str):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="'execution_mode' must be a string.",
                    )

                execution_mode = configured_mode.lower()

        if execution_mode not in {"sequential", "batch"}:
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

        Supported:

        {
            "execution_mode": "batch",
            "batch_size": 10
        }

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
    # Case evaluation
    # ------------------------------------------------------------------

    async def _evaluate_case(
        self,
        *,
        run: EvaluationRun,
        case: Any,
        response: Any,
        evaluator_configs: list[tuple[Evaluator, float]],
    ) -> None:
        """
        Evaluate and persist one successful model response.

        This method is shared by sequential and batch execution.
        """

        scores: dict[str, dict[str, Any]] = {}
        feedback_messages: list[str] = []

        # --------------------------------------------------------------
        # Run evaluators sequentially
        # --------------------------------------------------------------

        for evaluator, _weight in evaluator_configs:
            evaluation_score = await evaluator.evaluate(
                expected_output=case.expected_output,
                actual_output=response.output,
            )

            scores[evaluation_score.metric] = {
                "score": evaluation_score.score,
                "metadata": evaluation_score.metadata,
            }

            if evaluation_score.feedback:
                feedback_messages.append(f"{evaluation_score.metric}: {evaluation_score.feedback}")

        # --------------------------------------------------------------
        # Calculate overall score
        # --------------------------------------------------------------

        scoring_configuration: dict[str, Any] = {}

        if run.configuration:
            scoring_configuration = run.configuration.get(
                "scoring",
                {},
            )

        scoring_result = self.scoring_service.calculate(
            scores=scores,
            configuration=scoring_configuration,
        )

        scores["overall"] = {
            "score": scoring_result.score,
            "metadata": scoring_result.metadata,
        }

        # --------------------------------------------------------------
        # Build feedback
        # --------------------------------------------------------------

        feedback = "\n".join(feedback_messages) if feedback_messages else None

        # --------------------------------------------------------------
        # Persist result
        # --------------------------------------------------------------

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
        Persist a failed evaluation case.
        """

        await EvaluationResultService.create(
            self.db,
            evaluation_run_id=run.id,
            dataset_case_id=case.id,
            status="failed",
            actual_output=None,
            expected_output=case.expected_output,
            scores={},
            feedback=None,
            trace=None,
            latency_ms=None,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            error_message=str(exc),
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
    ) -> None:
        """
        Execute cases one at a time.

        Flow:

            case
              |
              v
        generate()
              |
              v
        evaluators
              |
              v
        scoring
              |
              v
        persist result
        """

        for case in cases:
            try:
                configuration = self._build_configuration(
                    model=model,
                    run=run,
                )

                response = await model_gateway.generate(
                    prompt=case.input,
                    configuration=configuration,
                )

                await self._evaluate_case(
                    run=run,
                    case=case,
                    response=response,
                    evaluator_configs=evaluator_configs,
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
    ) -> None:
        """
        Execute cases in batches.

        Model inference happens through generate_batch().

        Evaluation remains sequential inside each batch so that:

            batch
              |
              v
        generate_batch()
              |
              +--> case 1 -> evaluators -> scoring -> save
              |
              +--> case 2 -> evaluators -> scoring -> save
              |
              +--> case N -> evaluators -> scoring -> save
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

            # ----------------------------------------------------------
            # Model inference for the entire batch
            # ----------------------------------------------------------

            try:
                responses = await model_gateway.generate_batch(
                    prompts=prompts,
                    configuration=configuration,
                )

                if len(responses) != len(batch_cases):
                    raise RuntimeError("Model gateway returned an unexpected number of responses.")

            except Exception as exc:
                # ------------------------------------------------------
                # If batch inference fails, every case in that batch
                # is marked as failed.
                # ------------------------------------------------------

                for case in batch_cases:
                    await self._save_failed_case(
                        run=run,
                        case=case,
                        exc=exc,
                    )

                await self.db.commit()
                await self.db.refresh(run)

                continue

            # ----------------------------------------------------------
            # Evaluate each response sequentially
            # ----------------------------------------------------------

            for case, response in zip(
                batch_cases,
                responses,
                strict=True,
            ):
                try:
                    await self._evaluate_case(
                        run=run,
                        case=case,
                        response=response,
                        evaluator_configs=evaluator_configs,
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
        # 3. Resolve configuration
        # --------------------------------------------------------------

        evaluator_configs = self._get_evaluators(run)
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
        # 6. Load dataset cases
        # --------------------------------------------------------------

        cases = await DatasetCaseService.list(
            self.db,
            run.dataset_version_id,
        )

        run.total_cases = len(cases)
        run.completed_cases = 0
        run.failed_cases = 0
        run.status = EvaluationRunStatus.RUNNING

        await self.db.commit()
        await self.db.refresh(run)

        # --------------------------------------------------------------
        # 7. Execute according to configured mode
        # --------------------------------------------------------------

        if execution_mode == "sequential":
            await self._execute_sequential(
                run=run,
                cases=cases,
                model=model,
                evaluator_configs=evaluator_configs,
                model_gateway=model_gateway,
            )

        elif execution_mode == "batch":
            await self._execute_batch(
                run=run,
                cases=cases,
                model=model,
                evaluator_configs=evaluator_configs,
                model_gateway=model_gateway,
                batch_size=batch_size,
            )

        # --------------------------------------------------------------
        # 8. Complete evaluation run
        # --------------------------------------------------------------

        run.status = EvaluationRunStatus.COMPLETED

        await self.db.commit()
        await self.db.refresh(run)

        return run
