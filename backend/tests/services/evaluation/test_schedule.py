from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.evaluation import EvaluationScheduleType
from app.schemas.evaluation import (
    EvaluationScheduleCreate,
    EvaluationScheduleUpdate,
)
from app.services.evaluation import EvaluationScheduleService


@pytest.mark.asyncio
async def test_create_one_time_schedule():
    dataset_version = MagicMock()
    model = MagicMock()

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = model

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    next_run_at = datetime(
        2026,
        10,
        5,
        10,
        0,
        tzinfo=UTC,
    )

    data = EvaluationScheduleCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="One Time Evaluation",
        evaluation_type="text",
        schedule_type=EvaluationScheduleType.ONE_TIME,
        timezone="Asia/Kolkata",
        next_run_at=next_run_at,
    )

    schedule = await EvaluationScheduleService.create(
        db,
        data,
    )

    assert schedule.schedule_type == EvaluationScheduleType.ONE_TIME
    assert schedule.next_run_at == next_run_at
    assert schedule.schedule_expression is None
    assert schedule.is_active is True

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(schedule)


@pytest.mark.asyncio
async def test_create_recurring_schedule_calculates_next_run():
    dataset_version = MagicMock()
    model = MagicMock()

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = model

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    data = EvaluationScheduleCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Daily Evaluation",
        evaluation_type="text",
        schedule_type=EvaluationScheduleType.RECURRING,
        schedule_expression="0 10 * * *",
        timezone="Asia/Kolkata",
    )

    schedule = await EvaluationScheduleService.create(
        db,
        data,
    )

    assert schedule.schedule_type == EvaluationScheduleType.RECURRING
    assert schedule.schedule_expression == "0 10 * * *"
    assert schedule.next_run_at is not None
    assert schedule.next_run_at.tzinfo is not None
    assert schedule.is_active is True

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(schedule)


@pytest.mark.asyncio
async def test_create_rejects_invalid_timezone():
    dataset_version = MagicMock()
    model = MagicMock()

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = model

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    data = EvaluationScheduleCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Invalid Timezone",
        evaluation_type="text",
        schedule_type=EvaluationScheduleType.RECURRING,
        schedule_expression="0 10 * * *",
        timezone="Invalid/Timezone",
    )

    with pytest.raises(
        ValueError,
        match="Invalid timezone",
    ):
        await EvaluationScheduleService.create(
            db,
            data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_invalid_cron_expression():
    dataset_version = MagicMock()
    model = MagicMock()

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = model

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    data = EvaluationScheduleCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Invalid Cron",
        evaluation_type="text",
        schedule_type=EvaluationScheduleType.RECURRING,
        schedule_expression="invalid cron",
        timezone="Asia/Kolkata",
    )

    with pytest.raises(
        ValueError,
        match="Invalid schedule expression",
    ):
        await EvaluationScheduleService.create(
            db,
            data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_inactive_dataset_version():
    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = dataset_version_result

    data = EvaluationScheduleCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Inactive Dataset Version",
        evaluation_type="text",
        schedule_type=EvaluationScheduleType.ONE_TIME,
        timezone="UTC",
        next_run_at=datetime.now(UTC),
    )

    with pytest.raises(
        ValueError,
        match="Dataset version not found",
    ):
        await EvaluationScheduleService.create(
            db,
            data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_inactive_model():
    dataset_version = MagicMock()

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    data = EvaluationScheduleCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Inactive Model",
        evaluation_type="text",
        schedule_type=EvaluationScheduleType.ONE_TIME,
        timezone="UTC",
        next_run_at=datetime.now(UTC),
    )

    with pytest.raises(
        ValueError,
        match="Model not found",
    ):
        await EvaluationScheduleService.create(
            db,
            data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_by_id_returns_active_schedule():
    schedule = MagicMock()
    schedule.is_active = True

    result = MagicMock()
    result.scalar_one_or_none.return_value = schedule

    db = AsyncMock()
    db.execute.return_value = result

    returned_schedule = await EvaluationScheduleService.get_by_id(
        db,
        uuid4(),
    )

    assert returned_schedule == schedule
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_returns_active_schedules():
    schedule = MagicMock()
    schedule.is_active = True

    result = MagicMock()
    result.scalars.return_value.all.return_value = [schedule]

    db = AsyncMock()
    db.execute.return_value = result

    schedules = await EvaluationScheduleService.list(
        db,
    )

    assert schedules == [schedule]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_schedule():
    schedule = MagicMock()
    schedule.is_active = True

    db = AsyncMock()

    data = EvaluationScheduleUpdate(
        name="Updated Schedule",
        is_active=False,
    )

    updated_schedule = await EvaluationScheduleService.update(
        db,
        schedule,
        data,
    )

    assert schedule.name == "Updated Schedule"
    assert schedule.is_active is False
    assert updated_schedule == schedule

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(schedule)


@pytest.mark.asyncio
async def test_update_rejects_inactive_schedule():
    schedule = MagicMock()
    schedule.is_active = False

    db = AsyncMock()

    data = EvaluationScheduleUpdate(
        name="Updated Schedule",
    )

    with pytest.raises(
        ValueError,
        match="Evaluation schedule is inactive",
    ):
        await EvaluationScheduleService.update(
            db,
            schedule,
            data,
        )

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_soft_deletes_schedule():
    schedule = MagicMock()
    schedule.is_active = True

    db = AsyncMock()

    await EvaluationScheduleService.delete(
        db,
        schedule,
    )

    assert schedule.is_active is False
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_claim_due_returns_locked_schedules():
    schedule = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [schedule]

    db = AsyncMock()
    db.execute.return_value = result

    schedules = await EvaluationScheduleService.claim_due(
        db,
        limit=10,
    )

    assert schedules == [schedule]
    db.execute.assert_awaited_once()
