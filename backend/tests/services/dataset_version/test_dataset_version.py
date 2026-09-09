from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.dataset_version.version import DatasetVersionStatus
from app.schemas.dataset_version import (
    DatasetVersionCreate,
    DatasetVersionUpdate,
)
from app.services.dataset_version.dataset_version import DatasetVersionService


@pytest.mark.asyncio
async def test_create_dataset_version():
    db = AsyncMock()
    db.add = MagicMock()

    data = DatasetVersionCreate(
        dataset_id=uuid4(),
        version=1,
        status=DatasetVersionStatus.DRAFT,
        description="Initial version",
    )

    service = DatasetVersionService(db)

    version = await service.create(data)

    assert version.dataset_id == data.dataset_id
    assert version.version == data.version
    assert version.status == data.status
    assert version.description == data.description

    db.add.assert_called_once_with(version)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(version)


@pytest.mark.asyncio
async def test_create_dataset_version_rejects_duplicate_version():
    db = AsyncMock()
    db.add = MagicMock()

    db.commit.side_effect = IntegrityError(
        "duplicate key",
        {},
        Exception("duplicate"),
    )

    data = DatasetVersionCreate(
        dataset_id=uuid4(),
        version=1,
    )

    service = DatasetVersionService(db)

    with pytest.raises(
        HTTPException,
        match="This version already exists for this dataset.",
    ):
        await service.create(data)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_dataset_versions():
    dataset_id = uuid4()

    version_one = MagicMock()
    version_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        version_two,
        version_one,
    ]

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    versions = await service.list(dataset_id)

    assert versions == [version_two, version_one]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dataset_version_returns_version():
    version = MagicMock()
    version.id = uuid4()

    result = MagicMock()
    result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    returned = await service.get(version.id)

    assert returned == version
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dataset_version_raises_404_when_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    with pytest.raises(
        HTTPException,
        match="Dataset version not found.",
    ):
        await service.get(uuid4())


@pytest.mark.asyncio
async def test_update_dataset_version():
    version = MagicMock()
    version.status = DatasetVersionStatus.DRAFT
    version.description = "Old description"

    db = AsyncMock()

    data = DatasetVersionUpdate(
        description="Updated description",
    )

    service = DatasetVersionService(db)

    service.get = AsyncMock(return_value=version)

    updated = await service.update(version.id, data)

    assert updated == version
    assert version.description == "Updated description"

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(version)


@pytest.mark.asyncio
async def test_update_dataset_version_rejects_conflict():
    version = MagicMock()

    db = AsyncMock()

    db.commit.side_effect = IntegrityError(
        "duplicate key",
        {},
        Exception("duplicate"),
    )

    data = DatasetVersionUpdate(
        description="Updated description",
    )

    service = DatasetVersionService(db)

    service.get = AsyncMock(return_value=version)

    with pytest.raises(
        HTTPException,
        match="Unable to update dataset version.",
    ):
        await service.update(version.id, data)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_dataset_version():
    version = MagicMock()
    version.is_active = True

    db = AsyncMock()

    service = DatasetVersionService(db)

    service.get = AsyncMock(return_value=version)

    await service.delete(version.id)

    assert version.is_active is False

    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_finalize_dataset_version():
    version = MagicMock()
    version.id = uuid4()
    version.status = DatasetVersionStatus.DRAFT

    result = MagicMock()
    result.scalar_one_or_none.return_value = version

    cases_result = MagicMock()
    cases_result.all.return_value = [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]

    db = AsyncMock()
    db.execute.side_effect = [
        result,
        cases_result,
    ]

    service = DatasetVersionService(db)

    finalized = await service.finalize(version.id)

    assert finalized == version
    assert version.status == DatasetVersionStatus.READY
    assert version.case_count == 4

    assert version.analytics["case_count"] == 4
    assert version.analytics["reference_count"] == 2
    assert version.analytics["context_count"] == 2
    assert version.analytics["reference_coverage"] == 0.5
    assert version.analytics["context_coverage"] == 0.5

    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(version)


@pytest.mark.asyncio
async def test_finalize_dataset_version_rejects_non_draft():
    version = MagicMock()
    version.id = uuid4()
    version.status = DatasetVersionStatus.READY

    result = MagicMock()
    result.scalar_one_or_none.return_value = version

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    with pytest.raises(
        HTTPException,
        match="Only draft dataset versions can be finalized.",
    ):
        await service.finalize(version.id)

    db.execute.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_dataset_version_raises_404_when_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    with pytest.raises(
        HTTPException,
        match="Dataset version not found.",
    ):
        await service.finalize(uuid4())

    db.execute.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_dataset_version_ignores_inactive_cases():
    version = MagicMock()
    version.id = uuid4()
    version.status = DatasetVersionStatus.DRAFT

    result = MagicMock()
    result.scalar_one_or_none.return_value = version

    cases_result = MagicMock()

    # Only active cases are returned by the service query.
    cases_result.all.return_value = [
        (True, True),
        (False, True),
    ]

    db = AsyncMock()
    db.execute.side_effect = [
        result,
        cases_result,
    ]

    service = DatasetVersionService(db)

    finalized = await service.finalize(version.id)

    assert finalized.case_count == 2
    assert finalized.analytics["reference_count"] == 1
    assert finalized.analytics["context_count"] == 2
    assert finalized.analytics["reference_coverage"] == 0.5
    assert finalized.analytics["context_coverage"] == 1.0


@pytest.mark.asyncio
async def test_list_dataset_versions_excludes_inactive_versions():
    dataset_id = uuid4()

    active_version = MagicMock()
    active_version.is_active = True

    result = MagicMock()
    result.scalars.return_value.all.return_value = [active_version]

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    versions = await service.list(dataset_id)

    assert versions == [active_version]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dataset_version_raises_404_for_inactive_version():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    with pytest.raises(
        HTTPException,
        match="Dataset version not found.",
    ):
        await service.get(uuid4())

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_dataset_version_raises_404_when_not_found():
    db = AsyncMock()

    service = DatasetVersionService(db)

    service.get = AsyncMock(
        side_effect=HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )
    )

    with pytest.raises(
        HTTPException,
        match="Dataset version not found.",
    ):
        await service.delete(uuid4())

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_dataset_version_raises_404_for_inactive_version():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetVersionService(db)

    with pytest.raises(
        HTTPException,
        match="Dataset version not found.",
    ):
        await service.finalize(uuid4())

    db.execute.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
