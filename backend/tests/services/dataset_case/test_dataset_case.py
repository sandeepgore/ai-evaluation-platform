from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.dataset_version.version import DatasetVersionStatus
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
    dataset_version.status = DatasetVersionStatus.DRAFT

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    position_result = MagicMock()
    position_result.scalar_one.return_value = 0

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.side_effect = [
        version_result,
        position_result,
    ]

    data = DatasetCaseCreate(
        dataset_version_id=dataset_version.id,
        input="What is AI?",
        expected_output="Artificial Intelligence",
        case_metadata={"category": "general"},
    )

    case = await DatasetCaseService.create(db, data)

    assert case.dataset_version_id == data.dataset_version_id
    assert case.input == data.input
    assert case.expected_output == data.expected_output
    assert case.case_metadata == data.case_metadata

    assert case.position == 0

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
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.input = "Old input"
    case.expected_output = "Old output"
    case.case_metadata = None
    case.position = 1

    dataset_version = MagicMock()
    dataset_version.id = case.dataset_version_id
    dataset_version.status = DatasetVersionStatus.DRAFT

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    db = AsyncMock()
    db.execute.return_value = version_result

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
    assert case.has_reference is True
    assert case.has_context is False

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(case)


@pytest.mark.asyncio
async def test_delete_dataset_case_decrements_case_count():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()

    version = MagicMock()
    version.id = case.dataset_version_id
    version.status = DatasetVersionStatus.DRAFT
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

    assert case.is_active is False
    assert version.case_count == 2
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_dataset_case_does_not_decrement_below_zero():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()

    version = MagicMock()
    version.id = case.dataset_version_id
    version.status = DatasetVersionStatus.DRAFT
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

    assert case.is_active is False
    assert version.case_count == 0
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_dataset_case_rejects_ready_version():
    dataset_version = MagicMock()
    dataset_version.id = uuid4()
    dataset_version.case_count = 5
    dataset_version.status = DatasetVersionStatus.READY

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseCreate(
        dataset_version_id=dataset_version.id,
        input="What is AI?",
        expected_output="Artificial Intelligence",
    )

    with pytest.raises(
        HTTPException,
        match="Dataset cases can only be added to draft dataset versions.",
    ):
        await DatasetCaseService.create(db, data)

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_dataset_case_adds_reference_capability():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.expected_output = None
    case.case_metadata = None

    version = MagicMock()
    version.status = DatasetVersionStatus.DRAFT

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseUpdate(
        expected_output="Expected answer",
    )

    get_mock = AsyncMock(return_value=case)
    original_get = DatasetCaseService.get
    DatasetCaseService.get = get_mock

    try:
        updated = await DatasetCaseService.update(db, case.id, data)
    finally:
        DatasetCaseService.get = original_get

    assert updated == case
    assert case.has_reference is True
    assert case.has_context is False


@pytest.mark.asyncio
async def test_update_dataset_case_removes_reference_capability():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.expected_output = "Existing answer"
    case.case_metadata = None

    version = MagicMock()
    version.status = DatasetVersionStatus.DRAFT

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseUpdate(
        expected_output=None,
    )

    get_mock = AsyncMock(return_value=case)
    original_get = DatasetCaseService.get
    DatasetCaseService.get = get_mock

    try:
        updated = await DatasetCaseService.update(db, case.id, data)
    finally:
        DatasetCaseService.get = original_get

    assert updated == case
    assert case.has_reference is False
    assert case.has_context is False


@pytest.mark.asyncio
async def test_update_dataset_case_adds_context_capability():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.expected_output = None
    case.case_metadata = None

    version = MagicMock()
    version.status = DatasetVersionStatus.DRAFT

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseUpdate(
        case_metadata={
            "context": "Retrieved context",
        },
    )

    get_mock = AsyncMock(return_value=case)
    original_get = DatasetCaseService.get
    DatasetCaseService.get = get_mock

    try:
        updated = await DatasetCaseService.update(db, case.id, data)
    finally:
        DatasetCaseService.get = original_get

    assert updated == case
    assert case.has_reference is False
    assert case.has_context is True


@pytest.mark.asyncio
async def test_update_dataset_case_removes_context_capability():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.expected_output = None
    case.case_metadata = {
        "context": "Existing context",
    }

    version = MagicMock()
    version.status = DatasetVersionStatus.DRAFT

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseUpdate(
        case_metadata={},
    )

    get_mock = AsyncMock(return_value=case)
    original_get = DatasetCaseService.get
    DatasetCaseService.get = get_mock

    try:
        updated = await DatasetCaseService.update(db, case.id, data)
    finally:
        DatasetCaseService.get = original_get

    assert updated == case
    assert case.has_reference is False
    assert case.has_context is False


@pytest.mark.asyncio
async def test_update_dataset_case_rejects_ready_version():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()

    version = MagicMock()
    version.status = DatasetVersionStatus.READY

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = version_result

    data = DatasetCaseUpdate(
        input="Updated input",
    )

    get_mock = AsyncMock(return_value=case)
    original_get = DatasetCaseService.get
    DatasetCaseService.get = get_mock

    try:
        with pytest.raises(
            HTTPException,
            match="Dataset cases can only be updated in draft dataset versions.",
        ):
            await DatasetCaseService.update(db, case.id, data)
    finally:
        DatasetCaseService.get = original_get

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_dataset_case_rejects_ready_version():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()

    version = MagicMock()
    version.id = case.dataset_version_id
    version.status = DatasetVersionStatus.READY
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

    with pytest.raises(
        HTTPException,
        match="Dataset cases can only be deleted from draft dataset versions.",
    ):
        await DatasetCaseService.delete(
            db,
            case.id,
        )

    assert version.case_count == 3
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_dataset_cases_excludes_inactive_cases():
    dataset_version_id = uuid4()

    active_case = MagicMock()
    active_case.is_active = True

    inactive_case = MagicMock()
    inactive_case.is_active = False

    result = MagicMock()
    result.scalars.return_value.all.return_value = [active_case]

    db = AsyncMock()
    db.execute.return_value = result

    cases = await DatasetCaseService.list(
        db,
        dataset_version_id,
    )

    assert cases == [active_case]
    assert inactive_case not in cases


@pytest.mark.asyncio
async def test_update_dataset_case_rejects_inactive_case():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.is_active = False

    db = AsyncMock()
    DatasetCaseService.get = AsyncMock(return_value=case)

    with pytest.raises(
        HTTPException,
        match="Dataset case not found.",
    ):
        await DatasetCaseService.update(
            db,
            case.id,
            DatasetCaseUpdate(input="Updated input"),
        )

    db.execute.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_dataset_case_rejects_inactive_case():
    case = MagicMock()
    case.id = uuid4()
    case.dataset_version_id = uuid4()
    case.is_active = False

    db = AsyncMock()
    DatasetCaseService.get = AsyncMock(return_value=case)

    with pytest.raises(
        HTTPException,
        match="Dataset case not found.",
    ):
        await DatasetCaseService.delete(
            db,
            case.id,
        )

    db.execute.assert_not_awaited()
    db.commit.assert_not_awaited()
