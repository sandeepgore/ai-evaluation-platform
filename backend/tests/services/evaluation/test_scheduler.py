from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.evaluation import EvaluationScheduleType
from app.services.evaluation.scheduler import EvaluationScheduler


def build_schedule(
    *,
    schedule_type=EvaluationScheduleType.RECURRING,
    next_run_at=None,
    schedule_expression="0 10 * * *",
    timezone="Asia/Kolkata",
):
    schedule = MagicMock()

    schedule.id = "schedule-1"
    schedule.dataset_version_id = uuid4()
    schedule.model_id = uuid4()
    schedule.name = "Daily Evaluation"
    schedule.evaluation_type = "text"
    schedule.configuration = {"prompt": "{{input}}"}
    schedule.schedule_type = schedule_type
    schedule.schedule_expression = schedule_expression
    schedule.timezone = timezone
    schedule.next_run_at = next_run_at
    schedule.last_run_at = None
    schedule.is_active = True

    return schedule


@pytest.mark.asyncio
async def test_process_recurring_schedule_executes_when_late_by_less_than_one_hour():
    due_at = datetime(
        2026,
        10,
        4,
        4,
        30,
        tzinfo=UTC,
    )

    now = due_at + timedelta(minutes=30)

    schedule = build_schedule(
        next_run_at=due_at,
    )

    run = MagicMock()
    run.id = "run-1"

    db = AsyncMock()

    scheduler = EvaluationScheduler(
        queue=AsyncMock(),
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        create = AsyncMock(return_value=run)

        monkeypatch.setattr(
            "app.services.evaluation.scheduler.EvaluationRunService.create",
            create,
        )

        result = await scheduler._process_recurring_schedule(
            db,
            schedule,
            now,
        )

    assert result == "run-1"
    assert schedule.last_run_at == due_at
    assert schedule.next_run_at > due_at
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_recurring_schedule_skips_when_more_than_one_hour_late():
    due_at = datetime(
        2026,
        10,
        4,
        4,
        30,
        tzinfo=UTC,
    )

    now = due_at + timedelta(hours=5)

    schedule = build_schedule(
        next_run_at=due_at,
    )

    db = AsyncMock()

    scheduler = EvaluationScheduler(
        queue=AsyncMock(),
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        create = AsyncMock()

        monkeypatch.setattr(
            "app.services.evaluation.scheduler.EvaluationRunService.create",
            create,
        )

        result = await scheduler._process_recurring_schedule(
            db,
            schedule,
            now,
        )

    assert result is None
    assert create.await_count == 0
    assert schedule.last_run_at is None
    assert schedule.next_run_at > now
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_recurring_schedule_advances_when_run_creation_fails():
    due_at = datetime(
        2026,
        10,
        4,
        4,
        30,
        tzinfo=UTC,
    )

    schedule = build_schedule(
        next_run_at=due_at,
    )

    db = AsyncMock()

    scheduler = EvaluationScheduler(
        queue=AsyncMock(),
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.services.evaluation.scheduler.EvaluationRunService.create",
            AsyncMock(
                side_effect=ValueError(
                    "Dataset version not found",
                ),
            ),
        )

        result = await scheduler._process_recurring_schedule(
            db,
            schedule,
            due_at + timedelta(minutes=15),
        )

    assert result is None
    assert schedule.last_run_at is None
    assert schedule.next_run_at > due_at
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_one_time_schedule_deactivates_after_success():
    due_at = datetime(
        2026,
        10,
        4,
        10,
        0,
        tzinfo=UTC,
    )

    schedule = build_schedule(
        schedule_type=EvaluationScheduleType.ONE_TIME,
        next_run_at=due_at,
    )

    run = MagicMock()
    run.id = "run-1"

    db = AsyncMock()

    scheduler = EvaluationScheduler(
        queue=AsyncMock(),
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.services.evaluation.scheduler.EvaluationRunService.create",
            AsyncMock(return_value=run),
        )

        result = await scheduler._process_one_time_schedule(
            db,
            schedule,
            due_at,
        )

    assert result == "run-1"
    assert schedule.is_active is False
    assert schedule.next_run_at is None
    assert schedule.last_run_at == due_at
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_one_time_schedule_deactivates_when_run_creation_fails():
    due_at = datetime(
        2026,
        10,
        4,
        10,
        0,
        tzinfo=UTC,
    )

    schedule = build_schedule(
        schedule_type=EvaluationScheduleType.ONE_TIME,
        next_run_at=due_at,
    )

    db = AsyncMock()

    scheduler = EvaluationScheduler(
        queue=AsyncMock(),
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.services.evaluation.scheduler.EvaluationRunService.create",
            AsyncMock(
                side_effect=ValueError(
                    "Model not found",
                ),
            ),
        )

        result = await scheduler._process_one_time_schedule(
            db,
            schedule,
            due_at,
        )

    assert result is None
    assert schedule.is_active is False
    assert schedule.next_run_at is None
    assert schedule.last_run_at is None
    db.commit.assert_awaited_once()


def test_calculate_next_run_uses_schedule_timezone():
    schedule = build_schedule(
        schedule_expression="0 10 * * *",
        timezone="Asia/Kolkata",
    )

    base_time = datetime(
        2026,
        10,
        4,
        4,
        30,
        tzinfo=UTC,
    )

    next_run = EvaluationScheduler._calculate_next_run(
        schedule,
        base_time,
    )

    assert next_run == datetime(
        2026,
        10,
        5,
        4,
        30,
        tzinfo=UTC,
    )
