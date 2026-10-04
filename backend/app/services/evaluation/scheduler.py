from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.session import AsyncSessionLocal
from app.models.evaluation import EvaluationSchedule, EvaluationScheduleType
from app.schemas.evaluation import EvaluationRunCreate
from app.services.evaluation.evaluation import EvaluationRunService
from app.services.evaluation.schedule import EvaluationScheduleService
from app.services.evaluation_queue.evaluation_queue import EvaluationQueue
from app.workers.logging.log_cleanup import cleanup_old_logs
from app.workers.logging.scheduler_logger import SchedulerLogger


class EvaluationScheduler:
    """
    Scheduler for one-time and recurring evaluations.

    PostgreSQL is the source of truth for schedules and evaluation runs.
    Redis is used only to enqueue successfully created evaluation runs.

    One schedule is processed inside one database transaction so that
    evaluation-run creation and schedule advancement are atomic.
    """

    MISSED_SCHEDULE_GRACE_PERIOD = timedelta(hours=1)

    def __init__(
        self,
        queue: EvaluationQueue,
    ):
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        self.scheduler_id = f"{timestamp}-{uuid4().hex[:8]}"

        self.queue = queue
        self.shutdown_event = asyncio.Event()

        self.logger = SchedulerLogger(
            scheduler_id=self.scheduler_id,
        )

    def request_shutdown(self) -> None:
        """
        Request graceful scheduler shutdown.
        """
        self.shutdown_event.set()

    async def run_once(self) -> int:
        """
        Process all currently due schedules.

        Returns:
            Number of schedules processed.
        """
        processed = 0

        while True:
            async with AsyncSessionLocal() as db:
                schedules = await EvaluationScheduleService.claim_due(
                    db,
                    limit=1,
                )

                if not schedules:
                    return processed

                schedule = schedules[0]

                run_id = await self._process_schedule(
                    db,
                    schedule,
                )

            processed += 1

            if run_id is not None:
                await self._enqueue_run(
                    run_id,
                    schedule,
                )

    async def _process_schedule(
        self,
        db: AsyncSession,
        schedule: EvaluationSchedule,
    ) -> Any | None:
        """
        Create an evaluation run when the schedule should execute and
        advance/deactivate the schedule in the same transaction.

        Returns:
            Evaluation run ID when a run was created.
            None when the occurrence was skipped or run creation failed.
        """
        now = datetime.now(UTC)

        if schedule.schedule_type == EvaluationScheduleType.ONE_TIME:
            return await self._process_one_time_schedule(
                db,
                schedule,
                now,
            )

        return await self._process_recurring_schedule(
            db,
            schedule,
            now,
        )

    async def _process_one_time_schedule(
        self,
        db: AsyncSession,
        schedule: EvaluationSchedule,
        now: datetime,
    ) -> Any | None:
        """
        Execute an overdue one-time schedule once, then deactivate it.

        If run creation fails, the schedule is still deactivated so it
        cannot retry forever.
        """
        run_id = None

        try:
            evaluation_run = await EvaluationRunService.create(
                db,
                self._build_run_data(schedule),
                commit=False,
            )

            run_id = evaluation_run.id

        except ValueError:
            self.logger.exception(
                "Failed to create evaluation run for one-time schedule schedule_id=%s",
                schedule.id,
            )

        schedule.last_run_at = schedule.next_run_at if run_id is not None else schedule.last_run_at
        schedule.next_run_at = None
        schedule.is_active = False

        await db.commit()

        if run_id is None:
            self.logger.warning(
                "One-time schedule deactivated after failed execution schedule_id=%s",
                schedule.id,
            )

        return run_id

    async def _process_recurring_schedule(
        self,
        db: AsyncSession,
        schedule: EvaluationSchedule,
        now: datetime,
    ) -> Any | None:
        """
        Process one recurring occurrence.

        Rules:
        - <= 1 hour late: execute the missed occurrence once.
        - > 1 hour late: skip the missed occurrence(s).
        - Never replay historical backlog.
        """
        if schedule.next_run_at is None:
            raise ValueError("Recurring schedule is missing next_run_at.")

        due_at = schedule.next_run_at
        late_by = now - due_at

        if late_by <= self.MISSED_SCHEDULE_GRACE_PERIOD:
            return await self._execute_recurring_occurrence(
                db,
                schedule,
                due_at,
            )

        next_run_at = self._calculate_next_run(
            schedule,
            now,
        )

        self.logger.warning(
            "Skipping missed recurring schedule occurrence "
            "schedule_id=%s due_at=%s now=%s next_run_at=%s",
            schedule.id,
            due_at,
            now,
            next_run_at,
        )

        schedule.next_run_at = next_run_at

        await db.commit()

        return None

    async def _execute_recurring_occurrence(
        self,
        db: AsyncSession,
        schedule: EvaluationSchedule,
        due_at: datetime,
    ) -> Any | None:
        """
        Execute the current recurring occurrence.

        Run creation and schedule advancement happen in the same
        transaction. A validation failure still advances the schedule.
        """
        run_id = None

        try:
            evaluation_run = await EvaluationRunService.create(
                db,
                self._build_run_data(schedule),
                commit=False,
            )

            run_id = evaluation_run.id

        except ValueError:
            self.logger.exception(
                "Failed to create evaluation run for recurring schedule schedule_id=%s due_at=%s",
                schedule.id,
                due_at,
            )

        schedule.next_run_at = self._calculate_next_run(
            schedule,
            due_at,
        )

        if run_id is not None:
            schedule.last_run_at = due_at

        await db.commit()

        if run_id is None:
            self.logger.warning(
                "Recurring schedule advanced after failed execution schedule_id=%s next_run_at=%s",
                schedule.id,
                schedule.next_run_at,
            )

        return run_id

    @staticmethod
    def _calculate_next_run(
        schedule: EvaluationSchedule,
        base_time: datetime,
    ) -> datetime:
        """
        Calculate the next recurring occurrence strictly after base_time.
        """
        if schedule.schedule_expression is None:
            raise ValueError("Recurring schedule is missing schedule_expression.")

        try:
            timezone = ZoneInfo(schedule.timezone)

            base_local = base_time.astimezone(timezone)

            cron = croniter(
                schedule.schedule_expression,
                base_local,
            )

            return cron.get_next(datetime).astimezone(UTC)

        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError("Invalid recurring schedule configuration.") from exc

    @staticmethod
    def _build_run_data(
        schedule: EvaluationSchedule,
    ) -> EvaluationRunCreate:
        """
        Convert schedule configuration into an evaluation-run request.
        """
        return EvaluationRunCreate(
            dataset_version_id=schedule.dataset_version_id,
            model_id=schedule.model_id,
            name=schedule.name,
            evaluation_type=schedule.evaluation_type,
            configuration=schedule.configuration,
        )

    async def _enqueue_run(
        self,
        run_id: Any,
        schedule: EvaluationSchedule,
    ) -> None:
        """
        Enqueue a committed evaluation run.

        DB state is intentionally not rolled back when Redis enqueue fails.
        """
        try:
            await self.queue.enqueue(run_id)

            self.logger.info(
                "Scheduled evaluation enqueued schedule_id=%s run_id=%s",
                schedule.id,
                run_id,
            )

        except Exception:
            self.logger.exception(
                "Failed to enqueue scheduled evaluation "
                "schedule_id=%s run_id=%s. "
                "EvaluationRun remains PENDING.",
                schedule.id,
                run_id,
            )

    async def run_forever(self) -> None:
        """
        Run the scheduler polling loop.
        """
        await self.queue.initialize()

        deleted_logs = cleanup_old_logs()

        if deleted_logs:
            self.logger.info(
                "Evaluation log cleanup deleted %s old log file(s).",
                deleted_logs,
            )

        self.logger.info(
            "Evaluation scheduler started. poll_interval_seconds=%s",
            settings.scheduler_poll_interval_seconds,
        )

        try:
            while not self.shutdown_event.is_set():
                try:
                    processed = await self.run_once()

                    if processed:
                        self.logger.info(
                            "Evaluation scheduler processed %s schedule(s).",
                            processed,
                        )

                except Exception:
                    self.logger.exception("Unhandled evaluation scheduler error.")

                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=settings.scheduler_poll_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    continue

        finally:
            self.logger.info("Evaluation scheduler stopped.")
            self.logger.close()
