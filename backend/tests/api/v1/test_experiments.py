from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_fake_experiment():
    return SimpleNamespace(
        id=uuid4(),
        name="RAG Evaluation Experiment",
        description="Compare evaluation runs",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_create_experiment():
    experiment = create_fake_experiment()

    with patch(
        "app.api.v1.experiments.ExperimentService.create",
        new=AsyncMock(return_value=experiment),
    ) as create_mock:
        response = client.post(
            "/api/v1/experiments",
            json={
                "name": experiment.name,
                "description": experiment.description,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == str(experiment.id)
    assert data["name"] == experiment.name
    assert data["description"] == experiment.description
    assert data["is_active"] is True

    create_mock.assert_awaited_once()


def test_create_experiment_rejects_empty_name():
    response = client.post(
        "/api/v1/experiments",
        json={
            "name": "",
            "description": "Compare evaluation runs",
        },
    )

    assert response.status_code == 422


def test_create_experiment_rejects_name_over_150_characters():
    response = client.post(
        "/api/v1/experiments",
        json={
            "name": "x" * 151,
        },
    )

    assert response.status_code == 422


def test_get_experiment():
    experiment = create_fake_experiment()

    with patch(
        "app.api.v1.experiments.ExperimentService.get_by_id",
        new=AsyncMock(return_value=experiment),
    ):
        response = client.get(
            f"/api/v1/experiments/{experiment.id}"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(experiment.id)
    assert data["name"] == experiment.name
    assert data["description"] == experiment.description


def test_get_experiment_returns_404_when_not_found():
    with patch(
        "app.api.v1.experiments.ExperimentService.get_by_id",
        new=AsyncMock(return_value=None),
    ):
        response = client.get(
            f"/api/v1/experiments/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_list_experiments():
    experiment_one = create_fake_experiment()
    experiment_two = create_fake_experiment()

    with patch(
        "app.api.v1.experiments.ExperimentService.list",
        new=AsyncMock(return_value=[experiment_one, experiment_two]),
    ) as list_mock:
        response = client.get("/api/v1/experiments")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == str(experiment_one.id)
    assert data[1]["id"] == str(experiment_two.id)

    list_mock.assert_awaited_once_with(scope="recent")


def test_list_experiments_all_scope():
    experiment = create_fake_experiment()

    with patch(
        "app.api.v1.experiments.ExperimentService.list",
        new=AsyncMock(return_value=[experiment]),
    ) as list_mock:
        response = client.get(
            "/api/v1/experiments",
            params={"scope": "all"},
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(experiment.id)

    list_mock.assert_awaited_once_with(scope="all")


def test_list_experiments_rejects_invalid_scope():
    with patch(
        "app.api.v1.experiments.ExperimentService.list",
        new=AsyncMock(
            side_effect=ValueError(
                "Invalid experiment scope. Expected 'recent' or 'all'."
            )
        ),
    ):
        response = client.get(
            "/api/v1/experiments",
            params={"scope": "invalid"},
        )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid experiment scope. Expected 'recent' or 'all'."
    )


def test_delete_experiment():
    experiment = create_fake_experiment()

    with patch(
        "app.api.v1.experiments.ExperimentService.get_by_id",
        new=AsyncMock(return_value=experiment),
    ) as get_mock, patch(
        "app.api.v1.experiments.ExperimentService.delete",
        new=AsyncMock(),
    ) as delete_mock:
        response = client.delete(
            f"/api/v1/experiments/{experiment.id}"
        )

    assert response.status_code == 204
    assert response.content == b""

    get_mock.assert_awaited_once_with(experiment.id)
    delete_mock.assert_awaited_once_with(experiment)


def test_delete_experiment_returns_404_when_not_found():
    with patch(
        "app.api.v1.experiments.ExperimentService.get_by_id",
        new=AsyncMock(return_value=None),
    ) as get_mock, patch(
        "app.api.v1.experiments.ExperimentService.delete",
        new=AsyncMock(),
    ) as delete_mock:
        response = client.delete(
            f"/api/v1/experiments/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"

    get_mock.assert_awaited_once()
    delete_mock.assert_not_awaited()
