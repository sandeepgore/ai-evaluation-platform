from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_run import EvaluationRunMode
from app.schemas.evaluation import EvaluationRunCreate, EvaluationRunUpdate
from app.services.evaluation import EvaluationRunService
from app.services.evaluation.run_validation import (
    EvaluationRunValidationError,
)


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


@pytest.mark.asyncio
async def test_create_rejects_invalid_configuration_before_persistence():
    dataset_version_id = uuid4()
    model_id = uuid4()

    dataset_version = MagicMock()
    dataset_version.case_count = 8

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model = MagicMock()

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = model

    db = AsyncMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    data = EvaluationRunCreate(
        dataset_version_id=dataset_version_id,
        model_id=model_id,
        name="Invalid Strict Evaluation",
        evaluation_type="text",
        configuration={
            "data_policy": {
                "type": "strict",
            },
            "evaluators": [
                {
                    "name": "exact_match",
                }
            ],
        },
    )

    validation_error = EvaluationRunValidationError(
        {
            "message": "Evaluation run violates the configured data policy.",
            "policy": "strict",
            "requirement": "reference",
            "coverage": 0.5,
            "required_coverage": 1.0,
            "reason": "Strict policy requires complete reference coverage.",
        }
    )

    with patch(
        "app.services.evaluation.run_validation.EvaluationRunValidationService.validate",
        new=AsyncMock(side_effect=validation_error),
    ) as mock_validate:
        with pytest.raises(EvaluationRunValidationError) as exc_info:
            await EvaluationRunService.create(
                db,
                data,
            )

    assert exc_info.value.detail == validation_error.detail

    mock_validate.assert_awaited_once_with(
        db=db,
        dataset_version_id=dataset_version_id,
        evaluation_type="text",
        mode=EvaluationRunMode.DEFAULT,
        configuration=data.configuration,
    )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_inactive_run():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    run = await EvaluationRunService.get_by_id(
        db,
        uuid4(),
    )

    assert run is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_returns_active_runs_only():
    dataset_version_id = uuid4()

    active_run = MagicMock()
    active_run.is_active = True

    result = MagicMock()
    result.scalars.return_value.all.return_value = [active_run]

    db = AsyncMock()
    db.execute.return_value = result

    runs = await EvaluationRunService.list(
        db,
        dataset_version_id=dataset_version_id,
    )

    assert runs == [active_run]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_soft_deletes_evaluation_run():
    run = MagicMock()
    run.is_active = True

    db = AsyncMock()

    await EvaluationRunService.delete(
        db,
        run,
    )

    assert run.is_active is False
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_rejects_inactive_run():
    run = MagicMock()
    run.is_active = False

    db = AsyncMock()

    data = EvaluationRunUpdate(
        name="updated name",
    )

    with pytest.raises(
        ValueError,
        match="Evaluation run is inactive",
    ):
        await EvaluationRunService.update(
            db,
            run,
            data,
        )

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_inactive_dataset_version():
    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = dataset_version_result

    data = EvaluationRunCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Inactive Dataset Version Evaluation",
        evaluation_type="text",
        configuration={},
    )

    with pytest.raises(
        ValueError,
        match="Dataset version not found",
    ):
        await EvaluationRunService.create(
            db,
            data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_rejects_inactive_model():
    dataset_version = MagicMock()
    dataset_version.case_count = 8

    dataset_version_result = MagicMock()
    dataset_version_result.scalar_one_or_none.return_value = dataset_version

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.side_effect = [
        dataset_version_result,
        model_result,
    ]

    data = EvaluationRunCreate(
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="Inactive Model Evaluation",
        evaluation_type="text",
        configuration={},
    )

    with pytest.raises(
        ValueError,
        match="Model not found",
    ):
        await EvaluationRunService.create(
            db,
            data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
