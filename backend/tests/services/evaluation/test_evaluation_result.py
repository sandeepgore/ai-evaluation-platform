from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.evaluation_results.result import EvaluationResultService


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_inactive_result():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    evaluation_result = await EvaluationResultService.get_by_id(
        db,
        uuid4(),
    )

    assert evaluation_result is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_rejects_inactive_result():
    result = MagicMock()
    result.is_active = False

    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Evaluation result is inactive",
    ):
        await EvaluationResultService.update(
            db,
            result,
            feedback="updated feedback",
        )

    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_soft_deletes_evaluation_result():
    result = MagicMock()
    result.is_active = True

    db = AsyncMock()

    await EvaluationResultService.delete(
        db,
        result,
    )

    assert result.is_active is False
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_rejects_already_inactive_result():
    result = MagicMock()
    result.is_active = False

    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Evaluation result is already inactive",
    ):
        await EvaluationResultService.delete(
            db,
            result,
        )

    db.commit.assert_not_awaited()
