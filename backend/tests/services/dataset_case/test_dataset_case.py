from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.dataset_case import (
    DatasetCaseCreate,
    DatasetCaseUpdate,
)
from app.services.dataset_case.dataset_case import DatasetCaseService


@pytest.mark.asyncio
async def test_create_dataset_case():
    dataset_version = MagicMock()
    dataset_version.id = uuid4()
    dataset_version.case_count = 0

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = version_result

    data = DatasetCaseCreate(
        dataset_version_id=dataset_version.id,
        input="What is AI?",
        expected_output="Artificial Intelligence",
        case_metadata={"category": "general"},
        position=1,
    )

    case = await DatasetCaseService.create(db, data)

    assert case.dataset_version_id == data.dataset_version_id
    assert case.input == data.input
    assert case.expected_output == data.expected_output
    assert case.case_metadata == data.case_metadata
    assert case.position == data.position

    assert dataset_version.case_count == 1

    db.add.assert_called_once_with(case)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(case)


@pytest.mark.asyncio
async def test_create_dataset_case_raises_404_when_version_not_found():
    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseCreate(
        dataset_version_id=uuid4(),
        input="Test input",
    )

    with pytest.raises(
        HTTPException,
        match="Dataset version not found.",
    ):
        await DatasetCaseService.create(db, data)

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_dataset_cases():
    dataset_version_id = uuid4()

    case_one = MagicMock()
    case_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        case_one,
        case_two,
    ]

    db = AsyncMock()
    db.execute.return_value = result

    cases = await DatasetCaseService.list(
        db,
        dataset_version_id,
    )

    assert cases == [case_one, case_two]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dataset_case_returns_case():
    case = MagicMock()
    case.id = uuid4()

    result = MagicMock()
    result.scalar_one_or_none.return_value = case

    db = AsyncMock()
    db.execute.return_value = result

    returned = await DatasetCaseService.get(
        db,
        case.id,
    )

    assert returned == case
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dataset_case_raises_404_when_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    with pytest.raises(
        HTTPException,
        match="Dataset case not found.",
    ):
        await DatasetCaseService.get(
            db,
            uuid4(),
        )


@pytest.mark.asyncio
async def test_update_dataset_case():
    case = MagicMock()
    case.input = "Old input"
    case.expected_output = "Old output"
    case.position = 1

    db = AsyncMock()

    data = DatasetCaseUpdate(
        input="Updated input",
        expected_output="Updated output",
        position=2,
    )

    get_mock = AsyncMock(return_value=case)

    original_get = DatasetCaseService.get
    DatasetCaseService.get = get_mock

    try:
        updated = await DatasetCaseService.update(
            db,
            case.id,
            data,
        )
    finally:
        DatasetCaseService.get = original_get

    assert updated == case
    assert case.input == "Updated input"
    assert case.expected_output == "Updated output"
    assert case.position == 2

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(case)


@pytest.mark.asyncio
async def test_delete_dataset_case_decrements_case_count():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()

    version = MagicMock()
    version.id = case.dataset_version_id
    version.case_count = 3

    case_result = MagicMock()
    case_result.scalar_one_or_none.return_value = case

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.side_effect = [
        case_result,
        version_result,
    ]

    await DatasetCaseService.delete(
        db,
        case.id,
    )

    assert version.case_count == 2

    db.delete.assert_awaited_once_with(case)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_dataset_case_does_not_decrement_below_zero():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()

    version = MagicMock()
    version.id = case.dataset_version_id
    version.case_count = 0

    case_result = MagicMock()
    case_result.scalar_one_or_none.return_value = case

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.side_effect = [
        case_result,
        version_result,
    ]

    await DatasetCaseService.delete(
        db,
        case.id,
    )

    assert version.case_count == 0

    db.delete.assert_awaited_once_with(case)
    db.commit.assert_awaited_once()
