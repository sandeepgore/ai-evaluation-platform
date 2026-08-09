from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.model import Model
from app.services.dataset_case import DatasetCaseService
from app.services.evaluation import EvaluationRunService
from app.services.evaluation_results import EvaluationResultService
from app.services.model_gateway import ModelGateway


class EvaluationEngine:
    """
    Orchestrates the execution of an EvaluationRun.

    The engine is responsible for coordinating:
        EvaluationRun
            -> DatasetCases
            -> ModelGateway
            -> EvaluationResults
    """

    def __init__(
        self,
        db: AsyncSession,
        model_gateway: ModelGateway,
    ) -> None:
        self.db = db
        self.model_gateway = model_gateway

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
        # 3. Validate associated model
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
        # 4. Load dataset cases
        # ---------------------------------------------------------

        cases = await DatasetCaseService.list(
            self.db,
            run.dataset_version_id,
        )

        # Keep the run count synchronized with the actual cases.
        run.total_cases = len(cases)
        run.completed_cases = 0
        run.failed_cases = 0
        run.status = EvaluationRunStatus.RUNNING

        await self.db.commit()
        await self.db.refresh(run)

        # ---------------------------------------------------------
        # 5. Execute each case
        # ---------------------------------------------------------

        for case in cases:
            try:
                # -------------------------------------------------
                # Build model configuration
                # -------------------------------------------------

                configuration = {}

                if model.configuration:
                    configuration.update(model.configuration)

                if run.configuration:
                    configuration.update(run.configuration)

                # Preserve the database model information.
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
                # Persist successful result
                # -------------------------------------------------

                await EvaluationResultService.create(
                    self.db,
                    evaluation_run_id=run.id,
                    dataset_case_id=case.id,
                    status="completed",
                    actual_output=response.output,
                    expected_output=case.expected_output,
                    scores={},
                    feedback=None,
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
        # 6. Complete the evaluation run
        # ---------------------------------------------------------

        run.status = EvaluationRunStatus.COMPLETED

        await self.db.commit()
        await self.db.refresh(run)

        return run