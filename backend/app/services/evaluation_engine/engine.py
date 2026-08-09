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
from app.services.model_gateway import ModelGateway
from app.services.scoring import ScoringService


class EvaluationEngine:
    """
    Orchestrates the execution of an EvaluationRun.

    EvaluationRun
        -> DatasetCases
        -> ModelGateway
        -> EvaluatorRegistry
        -> ScoringService
        -> EvaluationResults
    """

    def __init__(
        self,
        db: AsyncSession,
        model_gateway: ModelGateway,
        evaluator_registry: EvaluatorRegistry,
        scoring_service: ScoringService,
    ) -> None:
        self.db = db
        self.model_gateway = model_gateway
        self.evaluator_registry = evaluator_registry
        self.scoring_service = scoring_service

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

        The evaluator weights are retained for backward compatibility,
        but score aggregation is delegated to ScoringService.
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
                        detail=(
                            "Each evaluator configuration must contain "
                            "a string 'name'."
                        ),
                    )

                if not isinstance(weight, (int, float)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Weight for evaluator '{evaluator_name}' "
                            "must be a number."
                        ),
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
                    detail=(
                        f"Evaluator '{evaluator_name}' "
                        "is configured more than once."
                    ),
                )

            if weight <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Weight for evaluator '{evaluator_name}' "
                        "must be greater than zero."
                    ),
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

    async def execute(
        self,
        run_id: UUID,
    ) -> EvaluationRun:
        """
        Execute all dataset cases belonging to an evaluation run.
        """

        # ---------------------------------------------------------
        # 1. Load evaluation run
        # ---------------------------------------------------------

        run = await EvaluationRunService.get_by_id(
            self.db,
            run_id,
        )

        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation run not found.",
            )

        # ---------------------------------------------------------
        # 2. Validate run state
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 3. Resolve evaluators
        # ---------------------------------------------------------

        evaluator_configs = self._get_evaluators(run)

        # ---------------------------------------------------------
        # 4. Validate associated model
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 5. Load dataset cases
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 6. Execute each case
        # ---------------------------------------------------------

        for case in cases:
            try:
                # -------------------------------------------------
                # Build model configuration
                # -------------------------------------------------

                configuration: dict[str, Any] = {}

                if model.configuration:
                    configuration.update(model.configuration)

                if run.configuration:
                    configuration.update(run.configuration)

                configuration.setdefault(
                    "model",
                    model.model_identifier,
                )

                # -------------------------------------------------
                # Invoke model gateway
                # -------------------------------------------------

                response = await self.model_gateway.generate(
                    prompt=case.input,
                    configuration=configuration,
                )

                # -------------------------------------------------
                # Run all evaluators
                # -------------------------------------------------

                scores: dict[str, dict[str, Any]] = {}
                feedback_messages: list[str] = []

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
                        feedback_messages.append(
                            f"{evaluation_score.metric}: "
                            f"{evaluation_score.feedback}"
                        )

                # -------------------------------------------------
                # Calculate overall score
                # -------------------------------------------------

                scoring_configuration = {}

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

                # -------------------------------------------------
                # Build feedback
                # -------------------------------------------------

                feedback = (
                    "\n".join(feedback_messages)
                    if feedback_messages
                    else None
                )

                # -------------------------------------------------
                # Persist successful result
                # -------------------------------------------------

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

            except Exception as exc:
                # -------------------------------------------------
                # Persist failed case
                # -------------------------------------------------

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

            # -----------------------------------------------------
            # Persist progress after each case
            # -----------------------------------------------------

            await self.db.commit()
            await self.db.refresh(run)

        # ---------------------------------------------------------
        # 7. Complete evaluation run
        # ---------------------------------------------------------

        run.status = EvaluationRunStatus.COMPLETED

        await self.db.commit()
        await self.db.refresh(run)

        return run