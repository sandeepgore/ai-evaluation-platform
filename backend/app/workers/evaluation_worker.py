import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event, current_thread
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.models.evaluation.evaluation_run import EvaluationRunStatus
from app.services.evaluation.evaluation import EvaluationRunService
from app.services.evaluation_engine.engine import EvaluationEngine
from app.services.evaluation_engine.scoring_config import (
    ScoringConfigurationService,
)
from app.services.evaluation_queue.evaluation_queue import EvaluationQueue
from app.services.evaluators.applicability import EvaluatorApplicabilityService
from app.services.evaluators.registry import create_default_registry
from app.services.scoring import ScoringService
from app.workers.logging.worker_logger import WorkerRunLogger


class EvaluationWorker:
    """
    Redis-backed evaluation worker.

    One evaluation run is owned by one worker thread from start to finish.
    PostgreSQL remains the source of truth for evaluation run state.
    Redis only transports evaluation run IDs.
    """

    def __init__(self):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        self.worker_id = f"{timestamp}-{uuid4().hex[:8]}"
        self.consumer_name = f"worker-{self.worker_id}"

        self.worker_count = settings.evaluation_worker_threads

        self.shutdown_event = Event()

        self.executor = ThreadPoolExecutor(
            max_workers=self.worker_count,
            thread_name_prefix="evaluation",
        )

    def request_shutdown(self) -> None:
        """
        Request graceful worker shutdown.

        The worker stops consuming new jobs but allows currently
        executing runs to finish.
        """
        self.shutdown_event.set()

    async def run(self) -> None:
        """
        Start consuming evaluation jobs.
        """
        redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

        queue = EvaluationQueue(
            redis=redis,
            stream=settings.evaluation_queue_stream,
            group=settings.evaluation_queue_group,
        )

        await queue.initialize()

        active_futures: set[Future] = set()

        try:
            while not self.shutdown_event.is_set():
                active_futures = {future for future in active_futures if not future.done()}

                if len(active_futures) >= self.worker_count:
                    await asyncio.sleep(0.1)
                    continue

                # Recover stale jobs before consuming new jobs.
                recovered_message = await queue.reclaim_stale(
                    consumer=self.consumer_name,
                )

                if recovered_message is not None:
                    message_id, evaluation_run_id = recovered_message

                    future = self.executor.submit(
                        self._process_message,
                        message_id,
                        evaluation_run_id,
                        True,
                    )

                    active_futures.add(future)
                    continue

                # No stale job available; consume a new job.
                message = await queue.consume(
                    consumer=self.consumer_name,
                    block_ms=1_000,
                )

                if message is None:
                    continue

                message_id, evaluation_run_id = message

                future = self.executor.submit(
                    self._process_message,
                    message_id,
                    evaluation_run_id,
                    False,
                )

                active_futures.add(future)
        finally:
            self.request_shutdown()

            self.executor.shutdown(
                wait=True,
            )

            await redis.aclose()

    def _process_message(
        self,
        message_id: str,
        evaluation_run_id: str,
        recovered: bool = False,
    ) -> None:
        """
        Process one Redis message inside one worker thread.

        Each thread owns its own asyncio event loop, DB session,
        and Redis client.
        """
        asyncio.run(
            self._process_message_async(
                message_id,
                evaluation_run_id,
                recovered,
            )
        )

    async def _refresh_claim_periodically(
        self,
        queue: EvaluationQueue,
        message_id: str,
        logger: WorkerRunLogger,
    ) -> None:
        """
        Periodically refresh the Redis pending-message claim.

        The refresh keeps a legitimately long-running evaluation owned
        by this worker so another worker does not reclaim it as stale.
        """
        refresh_interval = max(
            1,
            settings.evaluation_queue_claim_timeout_seconds // 3,
        )

        while True:
            await asyncio.sleep(refresh_interval)

            refreshed = await queue.refresh_claim(
                consumer=self.consumer_name,
                message_id=message_id,
            )

            if not refreshed:
                logger.warning(
                    "Redis claim could not be refreshed. "
                    "The message may no longer be owned by this worker."
                )

    async def _process_message_async(
        self,
        message_id: str,
        evaluation_run_id: str,
        recovered: bool = False,
    ) -> None:
        thread_name = current_thread().name

        logger = WorkerRunLogger(
            worker_id=self.worker_id,
            evaluation_run_id=evaluation_run_id,
            message_id=message_id,
            log_type="retry" if recovered else "execution",
        )

        redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

        queue = EvaluationQueue(
            redis=redis,
            stream=settings.evaluation_queue_stream,
            group=settings.evaluation_queue_group,
        )

        worker_engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            poolclass=NullPool,
        )

        worker_session_local = async_sessionmaker(
            bind=worker_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        claim_refresh_task: asyncio.Task | None = None

        try:
            logger.info(f"Job received by thread={thread_name}; message_id={message_id}")

            async with worker_session_local() as db:
                run_id = UUID(evaluation_run_id)

                if recovered:
                    run = await EvaluationRunService.get_running_for_recovery(
                        db,
                        run_id,
                    )
                else:
                    run = await EvaluationRunService.claim_pending(
                        db,
                        run_id,
                    )

                if run is None:
                    if recovered:
                        logger.info(
                            "Recovered run is no longer RUNNING. Message will be acknowledged."
                        )
                    else:
                        logger.info(
                            "Run was not claimed because it is no longer "
                            "in PENDING state. Message will be acknowledged."
                        )

                    await queue.acknowledge(message_id)
                    return

                if recovered:
                    logger.info("Running evaluation recovered successfully.")
                else:
                    logger.info("Run claimed successfully: PENDING -> RUNNING")

                evaluator_registry = create_default_registry()

                applicability_service = EvaluatorApplicabilityService(
                    evaluator_registry,
                )

                scoring_service = ScoringService()

                scoring_configuration_service = ScoringConfigurationService(
                    redis=redis,
                )

                engine = EvaluationEngine(
                    db=db,
                    model_gateway=None,
                    evaluator_registry=evaluator_registry,
                    applicability_service=applicability_service,
                    scoring_service=scoring_service,
                    scoring_configuration_service=(scoring_configuration_service),
                    redis=redis,
                )

                logger.info("Starting Redis claim refresh.")

                claim_refresh_task = asyncio.create_task(
                    self._refresh_claim_periodically(
                        queue=queue,
                        message_id=message_id,
                        logger=logger,
                    )
                )

                logger.info("Starting evaluation engine.")

                await engine.execute(
                    run_id,
                    claimed=True,
                    retry=recovered,
                )

                logger.info("Evaluation engine completed successfully.")

            await queue.acknowledge(message_id)

            logger.info("Redis message acknowledged.")

        except Exception:
            logger.exception("Unhandled worker execution error.")

            # The engine normally owns RUNNING -> FAILED.
            # This fallback protects against failures that happen
            # before the engine's main execution try/except block.
            await self._mark_run_failed_if_needed(
                evaluation_run_id,
                worker_session_local,
            )

            try:
                await queue.acknowledge(message_id)

                logger.info("Redis message acknowledged after failure.")
            except Exception:
                logger.exception("Failed to acknowledge Redis message after failure.")

        finally:
            if claim_refresh_task is not None:
                claim_refresh_task.cancel()

                try:
                    await claim_refresh_task
                except asyncio.CancelledError:
                    pass

            await worker_engine.dispose()
            await redis.aclose()
            logger.close()

    async def _mark_run_failed_if_needed(
        self,
        evaluation_run_id: str,
        session_local: async_sessionmaker[AsyncSession],
    ) -> None:
        """
        Safety fallback for exceptions escaping EvaluationEngine.

        If the engine already transitioned the run to FAILED,
        nothing is changed.
        """
        async with session_local() as db:
            run = await EvaluationRunService.get_by_id(
                db,
                UUID(evaluation_run_id),
            )

            if run is None:
                return

            if run.status != EvaluationRunStatus.RUNNING:
                return

            completed_at = datetime.now(timezone.utc)

            run.status = EvaluationRunStatus.FAILED
            run.completed_at = completed_at

            if run.started_at is not None:
                duration = (completed_at - run.started_at).total_seconds() * 1000

                run.duration_ms = int(duration)

            await db.commit()
