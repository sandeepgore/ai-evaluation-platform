from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.dataset.dataset import DatasetType
from app.schemas.dataset.dataset import DatasetCreate, DatasetUpdate
from app.services.dataset.dataset import DatasetService


@pytest.mark.asyncio
async def test_create_dataset():
    db = AsyncMock()
    db.add = MagicMock()

    data = DatasetCreate(
        project_id=uuid4(),
        name="Test Dataset",
        slug="test-dataset",
        description="Test dataset description",
        dataset_type=DatasetType.CUSTOM,
    )

    service = DatasetService(db)

    dataset = await service.create(data)

    assert dataset.project_id == data.project_id
    assert dataset.name == data.name
    assert dataset.slug == data.slug
    assert dataset.description == data.description
    assert dataset.dataset_type == data.dataset_type

    db.add.assert_called_once_with(dataset)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(dataset)


@pytest.mark.asyncio
async def test_create_dataset_rejects_duplicate_slug():
    db = AsyncMock()
    db.add = MagicMock()

    db.commit.side_effect = IntegrityError(
        "duplicate key",
        {},
        Exception("duplicate"),
    )

    data = DatasetCreate(
        project_id=uuid4(),
        name="Test Dataset",
        slug="test-dataset",
    )

    service = DatasetService(db)

    with pytest.raises(
        ValueError,
        match="A dataset with this slug already exists in this project.",
    ):
        await service.create(data)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_dataset_returns_dataset():
    dataset = MagicMock()
    dataset.id = uuid4()

    result = MagicMock()
    result.scalar_one_or_none.return_value = dataset

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetService(db)

    returned = await service.get(dataset.id)

    assert returned == dataset
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dataset_returns_none_when_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetService(db)

    dataset_id = uuid4()

    returned = await service.get(dataset_id)

    assert returned is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_datasets_by_project():
    project_id = uuid4()

    dataset_one = MagicMock()
    dataset_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        dataset_one,
        dataset_two,
    ]

    db = AsyncMock()
    db.execute.return_value = result

    service = DatasetService(db)

    datasets = await service.list_by_project(project_id)

    assert datasets == [dataset_one, dataset_two]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_dataset():
    dataset = MagicMock()
    dataset.name = "Old Dataset"
    dataset.slug = "old-dataset"
    dataset.description = "Old description"

    db = AsyncMock()

    data = DatasetUpdate(
        name="Updated Dataset",
        description="Updated description",
    )

    service = DatasetService(db)

    service.get = AsyncMock(return_value=dataset)

    updated = await service.update(dataset.id, data)

    assert updated == dataset
    assert dataset.name == "Updated Dataset"
    assert dataset.slug == "old-dataset"
    assert dataset.description == "Updated description"

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(dataset)


@pytest.mark.asyncio
async def test_update_dataset_returns_none_when_not_found():
    db = AsyncMock()

    data = DatasetUpdate(
        name="Updated Dataset",
    )

    service = DatasetService(db)

    service.get = AsyncMock(return_value=None)

    returned = await service.update(uuid4(), data)

    assert returned is None

    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_dataset_rejects_duplicate_slug():
    dataset = MagicMock()
    dataset.name = "Test Dataset"
    dataset.slug = "old-dataset"

    db = AsyncMock()

    db.commit.side_effect = IntegrityError(
        "duplicate key",
        {},
        Exception("duplicate"),
    )

    data = DatasetUpdate(
        slug="existing-dataset",
    )

    service = DatasetService(db)

    service.get = AsyncMock(return_value=dataset)

    with pytest.raises(
        ValueError,
        match="A dataset with this slug already exists in this project.",
    ):
        await service.update(dataset.id, data)

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_dataset():
    dataset = MagicMock()

    db = AsyncMock()

    service = DatasetService(db)

    service.get = AsyncMock(return_value=dataset)

    await service.delete(dataset.id)

    db.delete.assert_awaited_once_with(dataset)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_dataset_returns_false_when_not_found():
    db = AsyncMock()

    service = DatasetService(db)

    service.get = AsyncMock(return_value=None)

    deleted = await service.delete(uuid4())

    assert deleted is False

    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
