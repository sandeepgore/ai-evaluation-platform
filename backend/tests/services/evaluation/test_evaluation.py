from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.evaluation import EvaluationRunStatus
from app.services.evaluation import EvaluationRunService
from app.schemas.evaluation import EvaluationRunUpdate


def test_valid_pending_to_running_transition():
    assert EvaluationRunService.validate_status_transition(
        EvaluationRunStatus.PENDING,
        EvaluationRunStatus.RUNNING,
    )


def test_valid_pending_to_cancelled_transition():
    assert EvaluationRunService.validate_status_transition(
        EvaluationRunStatus.PENDING,
        EvaluationRunStatus.CANCELLED,
    )


def test_valid_running_to_completed_transition():
    assert EvaluationRunService.validate_status_transition(
        EvaluationRunStatus.RUNNING,
        EvaluationRunStatus.COMPLETED,
    )


def test_valid_running_to_failed_transition():
    assert EvaluationRunService.validate_status_transition(
        EvaluationRunStatus.RUNNING,
        EvaluationRunStatus.FAILED,
    )


def test_valid_running_to_cancelled_transition():
    assert EvaluationRunService.validate_status_transition(
        EvaluationRunStatus.RUNNING,
        EvaluationRunStatus.CANCELLED,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (EvaluationRunStatus.COMPLETED, EvaluationRunStatus.RUNNING),
        (EvaluationRunStatus.COMPLETED, EvaluationRunStatus.CANCELLED),
        (EvaluationRunStatus.FAILED, EvaluationRunStatus.RUNNING),
        (EvaluationRunStatus.FAILED, EvaluationRunStatus.COMPLETED),
        (EvaluationRunStatus.CANCELLED, EvaluationRunStatus.RUNNING),
        (EvaluationRunStatus.CANCELLED, EvaluationRunStatus.COMPLETED),
    ],
)
def test_invalid_status_transitions(
    current_status,
    new_status,
):
    with pytest.raises(ValueError):
        EvaluationRunService.validate_status_transition(
            current_status,
            new_status,
        )


def test_same_status_transition_is_allowed():
    assert EvaluationRunService.validate_status_transition(
        EvaluationRunStatus.PENDING,
        EvaluationRunStatus.PENDING,
    )


@pytest.mark.asyncio
async def test_update_allows_valid_status_transition():
    run = MagicMock()
    run.status = EvaluationRunStatus.PENDING

    db = AsyncMock()

    data = EvaluationRunUpdate(
        status=EvaluationRunStatus.RUNNING,
    )

    updated_run = await EvaluationRunService.update(
        db,
        run,
        data,
    )

    assert run.status == EvaluationRunStatus.RUNNING
    assert updated_run == run
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(run)


@pytest.mark.asyncio
async def test_update_rejects_invalid_status_transition():
    run = MagicMock()
    run.status = EvaluationRunStatus.COMPLETED

    db = AsyncMock()

    data = EvaluationRunUpdate(
        status=EvaluationRunStatus.RUNNING,
    )

    with pytest.raises(ValueError):
        await EvaluationRunService.update(
            db,
            run,
            data,
        )

    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
