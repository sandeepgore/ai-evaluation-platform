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
        status=DatasetVersionStatus.READY,
        description="Updated description",
    )

    service = DatasetVersionService(db)

    service.get = AsyncMock(return_value=version)

    updated = await service.update(version.id, data)

    assert updated == version
    assert version.status == DatasetVersionStatus.READY
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
        status=DatasetVersionStatus.READY,
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

    db = AsyncMock()

    service = DatasetVersionService(db)

    service.get = AsyncMock(return_value=version)

    await service.delete(version.id)

    db.delete.assert_awaited_once_with(version)
    db.commit.assert_awaited_once()
