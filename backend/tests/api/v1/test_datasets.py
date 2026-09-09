from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models.dataset_version.version import DatasetVersionStatus
from app.services.dataset_version import DatasetVersionService

client = TestClient(app)


def create_fake_dataset_version():
    return SimpleNamespace(
        id=uuid4(),
        dataset_id=uuid4(),
        version=1,
        status=DatasetVersionStatus.READY,
        description=None,
        case_count=2,
        is_active=True,
    )


def test_import_dataset():
    version = create_fake_dataset_version()

    payload = {
        "cases": [
            {
                "input": "What is RAG?",
                "expected_output": "Retrieval-Augmented Generation.",
                "metadata": {
                    "source": "test",
                },
            },
            {
                "input": "What is an embedding?",
                "expected_output": "A vector representation of data.",
                "metadata": {},
            },
        ]
    }

    with patch(
        "app.api.v1.datasets.DatasetImportService.import_json",
        new=AsyncMock(return_value=version),
    ) as import_mock:
        response = client.post(
            f"/api/v1/datasets/{version.dataset_id}/import",
            json=payload,
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == str(version.id)
    assert data["dataset_id"] == str(version.dataset_id)
    assert data["version"] == 1
    assert data["status"] == "ready"
    assert data["case_count"] == 2
    assert data["is_active"] is True

    import_mock.assert_awaited_once()


def test_finalize_dataset_version():
    version = create_fake_dataset_version()
    version.status = DatasetVersionStatus.READY

    with patch.object(
        DatasetVersionService,
        "finalize",
        new=AsyncMock(return_value=version),
    ) as finalize_mock:
        response = client.post(
            f"/api/v1/dataset-versions/{version.id}/finalize",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(version.id)
    assert data["dataset_id"] == str(version.dataset_id)
    assert data["version"] == 1
    assert data["status"] == "ready"
    assert data["case_count"] == 2
    assert data["is_active"] is True

    finalize_mock.assert_awaited_once_with(version.id)


def test_finalize_dataset_version_not_found():
    version_id = uuid4()

    with patch.object(
        DatasetVersionService,
        "finalize",
        new=AsyncMock(
            side_effect=HTTPException(
                status_code=404,
                detail="Dataset version not found.",
            )
        ),
    ) as finalize_mock:
        response = client.post(
            f"/api/v1/dataset-versions/{version_id}/finalize",
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset version not found."

    finalize_mock.assert_awaited_once_with(version_id)
