import asyncio
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from sqlalchemy import delete, select

from app.config.settings import settings
from app.db.session import AsyncSessionLocal, engine
from app.models.dataset.dataset import Dataset, DatasetType
from app.models.dataset_case.case import DatasetCase
from app.models.dataset_version.version import (
    DatasetVersion,
    DatasetVersionStatus,
)
from app.models.evaluation.evaluation_run import (
    EvaluationRun,
    EvaluationRunStatus,
)
from app.models.evaluation.evaluation_type import EvaluationType
from app.models.evaluation_result.evaluation_result import EvaluationResult
from app.models.model.model import Model, ModelProvider, ModelType
from app.models.organization.organization import Organization
from app.models.project.project import Project
from app.services.evaluation.evaluation import EvaluationRunService
from app.services.evaluation_queue.evaluation_queue import EvaluationQueue
from app.workers.evaluation_worker import EvaluationWorker


@pytest.mark.skip(
    reason="Worker integration tests temporarily isolated for NullPool/event-loop debugging"
)
@pytest.mark.asyncio
async def test_evaluation_worker_executes_run_with_case_level_na(
    monkeypatch,
    tmp_path,
):
    stream = f"evaluation:runs:test:{uuid4()}"
    group = f"evaluation-workers-test:{uuid4()}"

    monkeypatch.setattr(
        settings,
        "evaluation_queue_stream",
        stream,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_queue_group",
        group,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_log_directory",
        str(tmp_path),
    )
    monkeypatch.setattr(
        settings,
        "evaluation_worker_threads",
        1,
    )

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    organization_id = uuid4()

    try:
        async with AsyncSessionLocal() as db:
            organization = Organization(
                id=organization_id,
                name="Worker Integration Test Organization",
                slug=f"worker-integration-{uuid4().hex}",
            )

            project = Project(
                id=uuid4(),
                organization_id=organization.id,
                name="Worker Integration Test Project",
                slug=f"worker-integration-{uuid4().hex}",
            )

            dataset = Dataset(
                id=uuid4(),
                project_id=project.id,
                name="Worker Integration Test Dataset",
                slug=f"worker-integration-{uuid4().hex}",
                dataset_type=DatasetType.CUSTOM,
            )

            version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset.id,
                version=1,
                status=DatasetVersionStatus.READY,
                case_count=2,
                analytics={
                    "case_count": 2,
                    "reference_count": 1,
                    "context_count": 0,
                    "reference_coverage": 0.5,
                    "context_coverage": 0.0,
                },
            )

            executable_case = DatasetCase(
                id=uuid4(),
                dataset_version_id=version.id,
                input="What is the capital of France?",
                expected_output="Paris",
                has_reference=True,
                has_context=False,
                position=0,
            )

            na_case = DatasetCase(
                id=uuid4(),
                dataset_version_id=version.id,
                input="What is the capital of Germany?",
                expected_output=None,
                has_reference=False,
                has_context=False,
                position=1,
            )

            model = Model(
                id=uuid4(),
                project_id=project.id,
                name="Worker Integration Mock Model",
                provider=ModelProvider.MOCK,
                model_identifier="mock-model-v1",
                model_type=ModelType.CHAT,
                configuration={
                    "response_prefix": "Paris",
                },
            )

            run = EvaluationRun(
                id=uuid4(),
                dataset_version_id=version.id,
                model_id=model.id,
                name="Worker Integration N/A Test",
                evaluation_type=EvaluationType.TEXT,
                status=EvaluationRunStatus.PENDING,
                configuration={
                    "evaluators": ["contains"],
                    "data_policy": {
                        "type": "partial",
                    },
                },
            )

            db.add(organization)
            await db.flush()

            db.add(project)
            await db.flush()

            db.add(dataset)
            await db.flush()

            db.add(version)
            await db.flush()

            db.add_all(
                [
                    executable_case,
                    na_case,
                    model,
                ]
            )

            await db.flush()

            db.add(run)
            await db.commit()

            run_id = run.id
            executable_case_id = executable_case.id
            na_case_id = na_case.id

        queue = EvaluationQueue(
            redis=redis,
            stream=stream,
            group=group,
        )

        await queue.initialize()

        await queue.enqueue(run_id)

        worker = EvaluationWorker()
        worker_task = asyncio.create_task(worker.run())

        try:
            deadline = asyncio.get_running_loop().time() + 15

            while True:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(EvaluationRun).where(
                            EvaluationRun.id == run_id,
                        )
                    )
                    completed_run = result.scalar_one()

                    if completed_run.status in {
                        EvaluationRunStatus.COMPLETED,
                        EvaluationRunStatus.FAILED,
                    }:
                        break

                if asyncio.get_running_loop().time() >= deadline:
                    raise AssertionError("Evaluation worker did not finish within 15 seconds.")

                await asyncio.sleep(0.1)

            worker.request_shutdown()
            await worker_task

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(EvaluationRun).where(
                        EvaluationRun.id == run_id,
                    )
                )
                completed_run = result.scalar_one()

                assert completed_run.status == EvaluationRunStatus.COMPLETED
                assert completed_run.total_cases == 2
                assert completed_run.completed_cases == 1
                assert completed_run.failed_cases == 0
                assert completed_run.started_at is not None
                assert completed_run.completed_at is not None
                assert completed_run.duration_ms is not None

                result = await db.execute(
                    select(EvaluationResult).where(
                        EvaluationResult.evaluation_run_id == run_id,
                        EvaluationResult.dataset_case_id == executable_case_id,
                    )
                )
                executable_result = result.scalar_one()

                assert executable_result.status == "completed"
                assert executable_result.actual_output is not None
                assert "Paris" in executable_result.actual_output
                assert executable_result.scores is not None

                result = await db.execute(
                    select(EvaluationResult).where(
                        EvaluationResult.evaluation_run_id == run_id,
                        EvaluationResult.dataset_case_id == na_case_id,
                    )
                )
                na_result = result.scalar_one()

                assert na_result.status == "completed"
                assert na_result.actual_output is None
                assert na_result.scores is not None
                assert na_result.scores["overall"]["status"] == "not_applicable"
                assert na_result.trace is not None
                assert na_result.trace["model_called"] is False

            pending = await redis.xpending(
                stream,
                group,
            )

            assert pending["pending"] == 0

            log_files = list(tmp_path.rglob("*.log"))

            assert len(log_files) == 1
            assert log_files[0].name.startswith("execution_")

            log_content = log_files[0].read_text(
                encoding="utf-8",
            )

            assert "Job received" in log_content
            assert "Run claimed successfully" in log_content
            assert "Evaluation engine completed successfully" in log_content
            assert "Redis message acknowledged" in log_content

        finally:
            if not worker_task.done():
                worker.request_shutdown()
                await worker_task

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Organization).where(Organization.id == organization_id))
            await db.commit()

        await redis.delete(stream)
        await redis.aclose()
        await engine.dispose()


@pytest.mark.skip(
    reason="Worker integration tests temporarily isolated for NullPool/event-loop debugging"
)
@pytest.mark.asyncio
async def test_evaluation_worker_executes_two_runs_concurrently(
    monkeypatch,
    tmp_path,
):
    stream = f"evaluation:runs:test:{uuid4()}"
    group = f"evaluation-workers-test:{uuid4()}"

    monkeypatch.setattr(
        settings,
        "evaluation_queue_stream",
        stream,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_queue_group",
        group,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_log_directory",
        str(tmp_path),
    )
    monkeypatch.setattr(
        settings,
        "evaluation_worker_threads",
        2,
    )

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    organization_id = uuid4()
    run_ids = []

    try:
        async with AsyncSessionLocal() as db:
            organization = Organization(
                id=organization_id,
                name="Worker Concurrency Test Organization",
                slug=f"worker-concurrency-{uuid4().hex}",
            )

            project = Project(
                id=uuid4(),
                organization_id=organization.id,
                name="Worker Concurrency Test Project",
                slug=f"worker-concurrency-{uuid4().hex}",
            )

            dataset = Dataset(
                id=uuid4(),
                project_id=project.id,
                name="Worker Concurrency Test Dataset",
                slug=f"worker-concurrency-{uuid4().hex}",
                dataset_type=DatasetType.CUSTOM,
            )

            version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset.id,
                version=1,
                status=DatasetVersionStatus.READY,
                case_count=1,
                analytics={
                    "case_count": 1,
                    "reference_count": 1,
                    "context_count": 0,
                    "reference_coverage": 1.0,
                    "context_coverage": 0.0,
                },
            )

            case = DatasetCase(
                id=uuid4(),
                dataset_version_id=version.id,
                input="What is the capital of France?",
                expected_output="Paris",
                has_reference=True,
                has_context=False,
                position=0,
            )

            model = Model(
                id=uuid4(),
                project_id=project.id,
                name="Worker Concurrency Mock Model",
                provider=ModelProvider.MOCK,
                model_identifier="mock-model-v1",
                model_type=ModelType.CHAT,
                configuration={
                    "response_prefix": "Paris",
                },
            )

            run_a = EvaluationRun(
                id=uuid4(),
                dataset_version_id=version.id,
                model_id=model.id,
                name="Worker Concurrency Run A",
                evaluation_type=EvaluationType.TEXT,
                status=EvaluationRunStatus.PENDING,
                configuration={
                    "evaluators": ["contains"],
                    "data_policy": {
                        "type": "strict",
                    },
                },
            )

            run_b = EvaluationRun(
                id=uuid4(),
                dataset_version_id=version.id,
                model_id=model.id,
                name="Worker Concurrency Run B",
                evaluation_type=EvaluationType.TEXT,
                status=EvaluationRunStatus.PENDING,
                configuration={
                    "evaluators": ["contains"],
                    "data_policy": {
                        "type": "strict",
                    },
                },
            )

            db.add(organization)
            await db.flush()

            db.add(project)
            await db.flush()

            db.add(dataset)
            await db.flush()

            db.add(version)
            await db.flush()

            db.add_all(
                [
                    case,
                    model,
                ]
            )

            await db.flush()

            db.add_all(
                [
                    run_a,
                    run_b,
                ]
            )

            await db.commit()

            run_ids = [
                run_a.id,
                run_b.id,
            ]

        queue = EvaluationQueue(
            redis=redis,
            stream=stream,
            group=group,
        )

        await queue.initialize()

        await queue.enqueue(run_ids[0])
        await queue.enqueue(run_ids[1])

        worker = EvaluationWorker()
        worker_task = asyncio.create_task(worker.run())

        try:
            deadline = asyncio.get_running_loop().time() + 15

            while True:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(EvaluationRun).where(
                            EvaluationRun.id.in_(run_ids),
                        )
                    )

                    runs = result.scalars().all()

                    if len(runs) == 2 and all(
                        run.status
                        in {
                            EvaluationRunStatus.COMPLETED,
                            EvaluationRunStatus.FAILED,
                        }
                        for run in runs
                    ):
                        break

                if asyncio.get_running_loop().time() >= deadline:
                    raise AssertionError(
                        "Evaluation worker did not finish both runs within 15 seconds."
                    )

                await asyncio.sleep(0.1)

            worker.request_shutdown()
            await worker_task

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(EvaluationRun).where(
                        EvaluationRun.id.in_(run_ids),
                    )
                )

                runs = result.scalars().all()

                assert len(runs) == 2

                for completed_run in runs:
                    assert completed_run.status == EvaluationRunStatus.COMPLETED
                    assert completed_run.total_cases == 1
                    assert completed_run.completed_cases == 1
                    assert completed_run.failed_cases == 0
                    assert completed_run.started_at is not None
                    assert completed_run.completed_at is not None
                    assert completed_run.duration_ms is not None

                result = await db.execute(
                    select(EvaluationResult).where(
                        EvaluationResult.evaluation_run_id.in_(run_ids),
                    )
                )

                results = result.scalars().all()

                assert len(results) == 2

                for evaluation_result in results:
                    assert evaluation_result.status == "completed"
                    assert evaluation_result.actual_output is not None
                    assert "Paris" in evaluation_result.actual_output
                    assert evaluation_result.scores is not None

            pending = await redis.xpending(
                stream,
                group,
            )

            assert pending["pending"] == 0

            log_files = list(tmp_path.rglob("execution_*.log"))

            assert len(log_files) == 2

            log_contents = [log_file.read_text(encoding="utf-8") for log_file in log_files]

            assert all("Run claimed successfully" in content for content in log_contents)

            assert all(
                "Evaluation engine completed successfully" in content for content in log_contents
            )

            thread_names = set()

            for content in log_contents:
                for line in content.splitlines():
                    if "Job received by thread=" in line:
                        thread_name = line.split(
                            "Job received by thread=",
                            1,
                        )[1].split(";", 1)[0]

                        thread_names.add(thread_name)

            assert len(thread_names) == 2

        finally:
            if not worker_task.done():
                worker.request_shutdown()
                await worker_task

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Organization).where(Organization.id == organization_id))
            await db.commit()

        await redis.delete(stream)
        await redis.aclose()
        await engine.dispose()


@pytest.mark.skip(
    reason="Worker integration tests temporarily isolated for NullPool/event-loop debugging"
)
@pytest.mark.asyncio
async def test_evaluation_worker_ignores_duplicate_run_message(
    monkeypatch,
    tmp_path,
):
    stream = f"evaluation:runs:test:{uuid4()}"
    group = f"evaluation-workers-test:{uuid4()}"

    monkeypatch.setattr(
        settings,
        "evaluation_queue_stream",
        stream,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_queue_group",
        group,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_log_directory",
        str(tmp_path),
    )
    monkeypatch.setattr(
        settings,
        "evaluation_worker_threads",
        2,
    )

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    organization_id = uuid4()

    try:
        async with AsyncSessionLocal() as db:
            organization = Organization(
                id=organization_id,
                name="Worker Duplicate Test Organization",
                slug=f"worker-duplicate-{uuid4().hex}",
            )

            project = Project(
                id=uuid4(),
                organization_id=organization.id,
                name="Worker Duplicate Test Project",
                slug=f"worker-duplicate-{uuid4().hex}",
            )

            dataset = Dataset(
                id=uuid4(),
                project_id=project.id,
                name="Worker Duplicate Test Dataset",
                slug=f"worker-duplicate-{uuid4().hex}",
                dataset_type=DatasetType.CUSTOM,
            )

            version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset.id,
                version=1,
                status=DatasetVersionStatus.READY,
                case_count=1,
                analytics={
                    "case_count": 1,
                    "reference_count": 1,
                    "context_count": 0,
                    "reference_coverage": 1.0,
                    "context_coverage": 0.0,
                },
            )

            case = DatasetCase(
                id=uuid4(),
                dataset_version_id=version.id,
                input="What is the capital of France?",
                expected_output="Paris",
                has_reference=True,
                has_context=False,
                position=0,
            )

            model = Model(
                id=uuid4(),
                project_id=project.id,
                name="Worker Duplicate Mock Model",
                provider=ModelProvider.MOCK,
                model_identifier="mock-model-v1",
                model_type=ModelType.CHAT,
                configuration={
                    "response_prefix": "Paris",
                },
            )

            run = EvaluationRun(
                id=uuid4(),
                dataset_version_id=version.id,
                model_id=model.id,
                name="Worker Duplicate Run",
                evaluation_type=EvaluationType.TEXT,
                status=EvaluationRunStatus.PENDING,
                configuration={
                    "evaluators": ["contains"],
                    "data_policy": {
                        "type": "strict",
                    },
                },
            )

            db.add(organization)
            await db.flush()

            db.add(project)
            await db.flush()

            db.add(dataset)
            await db.flush()

            db.add(version)
            await db.flush()

            db.add_all(
                [
                    case,
                    model,
                ]
            )

            await db.flush()

            db.add(run)
            await db.commit()

            run_id = run.id
            case_id = case.id

        queue = EvaluationQueue(
            redis=redis,
            stream=stream,
            group=group,
        )

        await queue.initialize()

        # Intentionally enqueue the same run twice.
        await queue.enqueue(run_id)
        await queue.enqueue(run_id)

        worker = EvaluationWorker()
        worker_task = asyncio.create_task(worker.run())

        try:
            deadline = asyncio.get_running_loop().time() + 15

            while True:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(EvaluationRun).where(
                            EvaluationRun.id == run_id,
                        )
                    )

                    completed_run = result.scalar_one()

                    if completed_run.status in {
                        EvaluationRunStatus.COMPLETED,
                        EvaluationRunStatus.FAILED,
                    }:
                        break

                if asyncio.get_running_loop().time() >= deadline:
                    raise AssertionError("Evaluation worker did not finish within 15 seconds.")

                await asyncio.sleep(0.1)

            # Wait until the duplicate message has also been consumed.
            #
            # The first worker claims the run and executes it.
            # The second worker must consume the duplicate message,
            # fail the atomic claim, and acknowledge the message.
            log_deadline = asyncio.get_running_loop().time() + 10

            while True:
                log_files = list(tmp_path.rglob("execution_*.log"))

                log_contents = [log_file.read_text(encoding="utf-8") for log_file in log_files]

                skipped_logs = [
                    content
                    for content in log_contents
                    if ("Run was not claimed because it is no longer in PENDING state" in content)
                ]

                if skipped_logs:
                    break

                if asyncio.get_running_loop().time() >= log_deadline:
                    raise AssertionError(
                        "Duplicate evaluation message was not consumed by another worker."
                    )

                await asyncio.sleep(0.1)

            # The duplicate worker has reached the failed atomic claim.
            # Explicitly wait for both Redis messages to be acknowledged
            # before asserting that the pending-entry count is zero.
            ack_deadline = asyncio.get_running_loop().time() + 10

            while True:
                pending = await redis.xpending(
                    stream,
                    group,
                )

                if pending["pending"] == 0:
                    break

                if asyncio.get_running_loop().time() >= ack_deadline:
                    raise AssertionError(
                        "Evaluation worker did not acknowledge all duplicate "
                        f"messages. Pending={pending['pending']}"
                    )

                await asyncio.sleep(0.1)

            worker.request_shutdown()
            await worker_task

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(EvaluationRun).where(
                        EvaluationRun.id == run_id,
                    )
                )

                completed_run = result.scalar_one()

                assert completed_run.status == EvaluationRunStatus.COMPLETED

                result = await db.execute(
                    select(EvaluationResult).where(
                        EvaluationResult.evaluation_run_id == run_id,
                        EvaluationResult.dataset_case_id == case_id,
                    )
                )

                results = result.scalars().all()

                # Only one evaluation should have been executed.
                assert len(results) == 1

                assert results[0].status == "completed"
                assert results[0].actual_output is not None
                assert "Paris" in results[0].actual_output

            pending = await redis.xpending(
                stream,
                group,
            )

            assert pending["pending"] == 0

            log_files = list(tmp_path.rglob("execution_*.log"))

            # Both duplicate messages were consumed, but only one
            # worker successfully claimed and executed the run.
            assert len(log_files) == 2

            log_contents = [log_file.read_text(encoding="utf-8") for log_file in log_files]

            claimed_logs = [
                content for content in log_contents if "Run claimed successfully" in content
            ]

            skipped_logs = [
                content
                for content in log_contents
                if ("Run was not claimed because it is no longer in PENDING state" in content)
            ]

            assert len(claimed_logs) == 1
            assert len(skipped_logs) == 1

        finally:
            if not worker_task.done():
                worker.request_shutdown()
                await worker_task

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Organization).where(Organization.id == organization_id))
            await db.commit()

        await redis.delete(stream)
        await redis.aclose()
        await engine.dispose()


@pytest.mark.skip(
    reason="Worker integration tests temporarily isolated for NullPool/event-loop debugging"
)
@pytest.mark.asyncio
async def test_evaluation_worker_recovers_stale_running_run(
    monkeypatch,
    tmp_path,
):
    stream = f"evaluation:runs:test:{uuid4()}"
    group = f"evaluation-workers-test:{uuid4()}"

    monkeypatch.setattr(
        settings,
        "evaluation_queue_stream",
        stream,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_queue_group",
        group,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_log_directory",
        str(tmp_path),
    )
    monkeypatch.setattr(
        settings,
        "evaluation_worker_threads",
        1,
    )
    monkeypatch.setattr(
        settings,
        "evaluation_queue_claim_timeout_seconds",
        3,
    )

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    organization_id = uuid4()

    try:
        async with AsyncSessionLocal() as db:
            organization = Organization(
                id=organization_id,
                name="Worker Recovery Test Organization",
                slug=f"worker-recovery-{uuid4().hex}",
            )

            project = Project(
                id=uuid4(),
                organization_id=organization.id,
                name="Worker Recovery Test Project",
                slug=f"worker-recovery-{uuid4().hex}",
            )

            dataset = Dataset(
                id=uuid4(),
                project_id=project.id,
                name="Worker Recovery Test Dataset",
                slug=f"worker-recovery-{uuid4().hex}",
                dataset_type=DatasetType.CUSTOM,
            )

            version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset.id,
                version=1,
                status=DatasetVersionStatus.READY,
                case_count=1,
                analytics={
                    "case_count": 1,
                    "reference_count": 1,
                    "context_count": 0,
                    "reference_coverage": 1.0,
                    "context_coverage": 0.0,
                },
            )

            case = DatasetCase(
                id=uuid4(),
                dataset_version_id=version.id,
                input="What is the capital of France?",
                expected_output="Paris",
                has_reference=True,
                has_context=False,
                position=0,
            )

            model = Model(
                id=uuid4(),
                project_id=project.id,
                name="Worker Recovery Mock Model",
                provider=ModelProvider.MOCK,
                model_identifier="mock-model-v1",
                model_type=ModelType.CHAT,
                configuration={
                    "response_prefix": "Paris",
                },
            )

            run = EvaluationRun(
                id=uuid4(),
                dataset_version_id=version.id,
                model_id=model.id,
                name="Worker Recovery Run",
                evaluation_type=EvaluationType.TEXT,
                status=EvaluationRunStatus.PENDING,
                configuration={
                    "evaluators": ["contains"],
                    "data_policy": {
                        "type": "strict",
                    },
                },
            )

            db.add(organization)
            await db.flush()

            db.add(project)
            await db.flush()

            db.add(dataset)
            await db.flush()

            db.add(version)
            await db.flush()

            db.add_all(
                [
                    case,
                    model,
                ]
            )
            await db.flush()

            db.add(run)
            await db.commit()

            run_id = run.id
            case_id = case.id

        queue = EvaluationQueue(
            redis=redis,
            stream=stream,
            group=group,
        )

        await queue.initialize()

        message_id = await queue.enqueue(run_id)

        # Simulate a worker consuming the message and then disappearing.
        # The message remains pending in the consumer group's PEL.
        consumed = await redis.xreadgroup(
            groupname=group,
            consumername="crashed-worker",
            streams={stream: ">"},
            count=1,
            block=1_000,
        )

        assert consumed

        _stream_name, entries = consumed[0]
        consumed_message_id, data = entries[0]

        assert str(consumed_message_id) == message_id
        assert str(data["evaluation_run_id"]) == str(run_id)

        # Simulate the database state at the moment the worker crashes.
        async with AsyncSessionLocal() as db:
            claimed_run = await EvaluationRunService.claim_pending(
                db,
                run_id,
            )

            assert claimed_run is not None
            assert claimed_run.status == EvaluationRunStatus.RUNNING

        pending = await redis.xpending(
            stream,
            group,
        )

        assert pending["pending"] == 1

        # Wait until the Redis message is eligible for recovery.
        stale_deadline = asyncio.get_running_loop().time() + 10

        while True:
            pending_messages = await redis.xpending_range(
                stream,
                group,
                min="-",
                max="+",
                count=10,
            )

            assert pending_messages

            idle_ms = pending_messages[0]["time_since_delivered"]

            if idle_ms >= 3_000:
                break

            if asyncio.get_running_loop().time() >= stale_deadline:
                raise AssertionError(
                    "Evaluation queue message did not become stale within 10 seconds."
                )

            await asyncio.sleep(0.1)

        worker = EvaluationWorker()
        worker_task = asyncio.create_task(worker.run())

        try:
            deadline = asyncio.get_running_loop().time() + 15

            while True:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(EvaluationRun).where(
                            EvaluationRun.id == run_id,
                        )
                    )

                    recovered_run = result.scalar_one()

                    if recovered_run.status in {
                        EvaluationRunStatus.COMPLETED,
                        EvaluationRunStatus.FAILED,
                    }:
                        break

                if asyncio.get_running_loop().time() >= deadline:
                    raise AssertionError(
                        "Evaluation worker did not recover the run within 15 seconds."
                    )

                await asyncio.sleep(0.1)

            # Explicitly wait for the recovered Redis message to be acknowledged.
            ack_deadline = asyncio.get_running_loop().time() + 10

            while True:
                pending = await redis.xpending(
                    stream,
                    group,
                )

                if pending["pending"] == 0:
                    break

                if asyncio.get_running_loop().time() >= ack_deadline:
                    raise AssertionError(
                        "Recovered evaluation message was not acknowledged. "
                        f"Pending={pending['pending']}"
                    )

                await asyncio.sleep(0.1)

            worker.request_shutdown()
            await worker_task

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(EvaluationRun).where(
                        EvaluationRun.id == run_id,
                    )
                )

                recovered_run = result.scalar_one()

                assert recovered_run.status == EvaluationRunStatus.COMPLETED
                assert recovered_run.total_cases == 1
                assert recovered_run.completed_cases == 1
                assert recovered_run.failed_cases == 0
                assert recovered_run.started_at is not None
                assert recovered_run.completed_at is not None
                assert recovered_run.duration_ms is not None

                result = await db.execute(
                    select(EvaluationResult).where(
                        EvaluationResult.evaluation_run_id == run_id,
                        EvaluationResult.dataset_case_id == case_id,
                    )
                )

                evaluation_results = result.scalars().all()

                assert len(evaluation_results) == 1
                assert evaluation_results[0].status == "completed"
                assert evaluation_results[0].actual_output is not None
                assert "Paris" in evaluation_results[0].actual_output
                assert evaluation_results[0].scores is not None

            pending = await redis.xpending(
                stream,
                group,
            )

            assert pending["pending"] == 0

            retry_logs = list(tmp_path.rglob("retry_*.log"))

            assert len(retry_logs) == 1

            log_content = retry_logs[0].read_text(
                encoding="utf-8",
            )

            assert "Job received" in log_content
            assert "Running evaluation recovered successfully" in log_content
            assert "Evaluation engine completed successfully" in log_content
            assert "Redis message acknowledged" in log_content

        finally:
            if not worker_task.done():
                worker.request_shutdown()
                await worker_task

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Organization).where(
                    Organization.id == organization_id,
                )
            )
            await db.commit()

        await redis.delete(stream)
        await redis.aclose()
        await engine.dispose()
