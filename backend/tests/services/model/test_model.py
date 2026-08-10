from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.model import ModelProvider, ModelType
from app.schemas.model import ModelCreate, ModelUpdate
from app.services.model.model import ModelService


def create_model():
    model = MagicMock()
    model.id = uuid4()
    model.project_id = uuid4()
    model.name = "Test Model"
    model.provider = ModelProvider.MOCK
    model.model_identifier = "test-model"
    model.model_type = ModelType.CHAT
    model.configuration = {"temperature": 0.7}
    model.is_active = True
    return model


@pytest.mark.asyncio
async def test_create_model():
    db = AsyncMock()
    db.add = MagicMock()

    data = ModelCreate(
        project_id=uuid4(),
        name="Test Model",
        provider=ModelProvider.MOCK,
        model_identifier="test-model",
        model_type=ModelType.CHAT,
        configuration={"temperature": 0.7},
    )

    service = ModelService(db)

    model = await service.create(data)

    assert model.project_id == data.project_id
    assert model.name == data.name
    assert model.provider == data.provider
    assert model.model_identifier == data.model_identifier
    assert model.model_type == data.model_type
    assert model.configuration == data.configuration

    db.add.assert_called_once_with(model)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(model)


@pytest.mark.asyncio
async def test_create_model_rejects_duplicate_provider_and_identifier():
    db = AsyncMock()
    db.add = MagicMock()

    data = ModelCreate(
        project_id=uuid4(),
        name="Test Model",
        provider=ModelProvider.OPENAI,
        model_identifier="gpt-4",
    )

    db.commit.side_effect = IntegrityError(
        "duplicate key",
        {},
        Exception("duplicate"),
    )

    service = ModelService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.create(data)

    assert exc_info.value.status_code == 409
    assert (
        exc_info.value.detail
        == "A model with this provider and identifier already exists in this project."
    )

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_model_returns_model():
    model = create_model()

    result = MagicMock()
    result.scalar_one_or_none.return_value = model

    db = AsyncMock()
    db.execute.return_value = result

    service = ModelService(db)

    returned = await service.get(model.id)

    assert returned == model

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_model_raises_404_when_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = ModelService(db)

    model_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await service.get(model_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Model not found"

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_models_by_project():
    project_id = uuid4()

    model_one = create_model()
    model_two = create_model()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        model_one,
        model_two,
    ]

    db = AsyncMock()
    db.execute.return_value = result

    service = ModelService(db)

    models = await service.list(project_id)

    assert models == [model_one, model_two]

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_model():
    model = create_model()

    db = AsyncMock()

    service = ModelService(db)

    service.get = AsyncMock(return_value=model)

    data = ModelUpdate(
        name="Updated Model",
        model_identifier="updated-model",
        configuration={"temperature": 0.2},
        is_active=False,
    )

    updated = await service.update(model.id, data)

    assert updated == model
    assert model.name == "Updated Model"
    assert model.model_identifier == "updated-model"
    assert model.configuration == {"temperature": 0.2}
    assert model.is_active is False

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(model)


@pytest.mark.asyncio
async def test_update_model_allows_partial_update():
    model = create_model()

    db = AsyncMock()

    service = ModelService(db)

    service.get = AsyncMock(return_value=model)

    data = ModelUpdate(
        name="Updated Model",
    )

    updated = await service.update(model.id, data)

    assert updated == model
    assert model.name == "Updated Model"
    assert model.model_identifier == "test-model"
    assert model.provider == ModelProvider.MOCK

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(model)


@pytest.mark.asyncio
async def test_update_model_rejects_duplicate_provider_and_identifier():
    model = create_model()

    db = AsyncMock()

    db.commit.side_effect = IntegrityError(
        "duplicate key",
        {},
        Exception("duplicate"),
    )

    service = ModelService(db)
    service.get = AsyncMock(return_value=model)

    data = ModelUpdate(
        provider=ModelProvider.OPENAI,
        model_identifier="gpt-4",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update(model.id, data)

    assert exc_info.value.status_code == 409
    assert (
        exc_info.value.detail
        == "A model with this provider and identifier already exists in this project."
    )

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_model_raises_404_when_not_found():
    db = AsyncMock()

    service = ModelService(db)
    service.get = AsyncMock(
        side_effect=HTTPException(
            status_code=404,
            detail="Model not found",
        )
    )

    data = ModelUpdate(name="Updated Model")

    with pytest.raises(HTTPException) as exc_info:
        await service.update(uuid4(), data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Model not found"

    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_model():
    model = create_model()

    db = AsyncMock()

    service = ModelService(db)
    service.get = AsyncMock(return_value=model)

    await service.delete(model.id)

    db.delete.assert_awaited_once_with(model)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_model_raises_404_when_not_found():
    db = AsyncMock()

    service = ModelService(db)
    service.get = AsyncMock(
        side_effect=HTTPException(
            status_code=404,
            detail="Model not found",
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.delete(uuid4())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Model not found"

    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
