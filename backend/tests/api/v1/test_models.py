from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.model import ModelProvider, ModelType

client = TestClient(app)


def create_fake_model():
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        name="GPT Test Model",
        provider=ModelProvider.OPENAI,
        model_identifier="gpt-test",
        model_type=ModelType.CHAT,
        configuration={
            "temperature": 0.2,
            "max_tokens": 1000,
        },
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_create_model():
    model = create_fake_model()

    with patch(
        "app.api.v1.models.ModelService.create",
        new=AsyncMock(return_value=model),
    ):
        response = client.post(
            "/api/v1/models",
            json={
                "project_id": str(model.project_id),
                "name": model.name,
                "provider": model.provider.value,
                "model_identifier": model.model_identifier,
                "model_type": model.model_type.value,
                "configuration": model.configuration,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == str(model.id)
    assert data["project_id"] == str(model.project_id)
    assert data["name"] == model.name
    assert data["provider"] == model.provider.value
    assert data["model_identifier"] == model.model_identifier
    assert data["model_type"] == model.model_type.value
    assert data["configuration"] == model.configuration
    assert data["is_active"] is True


def test_create_model_uses_default_model_type():
    model = create_fake_model()

    with patch(
        "app.api.v1.models.ModelService.create",
        new=AsyncMock(return_value=model),
    ):
        response = client.post(
            "/api/v1/models",
            json={
                "project_id": str(model.project_id),
                "name": model.name,
                "provider": model.provider.value,
                "model_identifier": model.model_identifier,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["model_type"] == model.model_type.value


def test_create_model_rejects_invalid_project_id():
    response = client.post(
        "/api/v1/models",
        json={
            "project_id": "not-a-uuid",
            "name": "GPT Test Model",
            "provider": "openai",
            "model_identifier": "gpt-test",
        },
    )

    assert response.status_code == 422


def test_create_model_rejects_empty_name():
    response = client.post(
        "/api/v1/models",
        json={
            "project_id": str(uuid4()),
            "name": "",
            "provider": "openai",
            "model_identifier": "gpt-test",
        },
    )

    assert response.status_code == 422


def test_get_model():
    model = create_fake_model()

    with patch(
        "app.api.v1.models.ModelService.get",
        new=AsyncMock(return_value=model),
    ):
        response = client.get(f"/api/v1/models/{model.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(model.id)
    assert data["name"] == model.name
    assert data["provider"] == model.provider.value


def test_get_model_returns_404_when_not_found():
    with patch(
        "app.api.v1.models.ModelService.get",
        new=AsyncMock(
            side_effect=__import__("fastapi").HTTPException(
                status_code=404,
                detail="Model not found",
            )
        ),
    ):
        response = client.get(f"/api/v1/models/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Model not found"


def test_list_models():
    project_id = uuid4()

    model_one = create_fake_model()
    model_one.project_id = project_id

    model_two = create_fake_model()
    model_two.project_id = project_id

    with patch(
        "app.api.v1.models.ModelService.list",
        new=AsyncMock(return_value=[model_one, model_two]),
    ):
        response = client.get(
            "/api/v1/models",
            params={"project_id": str(project_id)},
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == str(model_one.id)
    assert data[1]["id"] == str(model_two.id)


def test_list_models_requires_project_id():
    response = client.get("/api/v1/models")

    assert response.status_code == 422


def test_update_model():
    model = create_fake_model()
    model.name = "Updated Model"

    with patch(
        "app.api.v1.models.ModelService.update",
        new=AsyncMock(return_value=model),
    ):
        response = client.patch(
            f"/api/v1/models/{model.id}",
            json={
                "name": "Updated Model",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(model.id)
    assert data["name"] == "Updated Model"


def test_update_model_allows_partial_update():
    model = create_fake_model()

    with patch(
        "app.api.v1.models.ModelService.update",
        new=AsyncMock(return_value=model),
    ):
        response = client.patch(
            f"/api/v1/models/{model.id}",
            json={
                "is_active": False,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(model.id)
    assert data["is_active"] is True


def test_delete_model():
    model = create_fake_model()

    with patch(
        "app.api.v1.models.ModelService.delete",
        new=AsyncMock(),
    ) as delete_mock:
        response = client.delete(f"/api/v1/models/{model.id}")

    assert response.status_code == 204
    assert response.content == b""

    delete_mock.assert_awaited_once_with(model.id)
