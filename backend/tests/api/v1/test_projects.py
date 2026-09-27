from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_fake_project():
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        name="Test Project",
        slug="test-project",
        description="Test project description",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_create_project():
    project = create_fake_project()

    with patch(
        "app.api.v1.projects.ProjectService.create",
        new=AsyncMock(return_value=project),
    ) as create_mock:
        response = client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(project.organization_id),
                "name": project.name,
                "slug": project.slug,
                "description": project.description,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == str(project.id)
    assert data["organization_id"] == str(project.organization_id)
    assert data["name"] == project.name
    assert data["slug"] == project.slug
    assert data["description"] == project.description
    assert data["is_active"] is True

    create_mock.assert_awaited_once()


def test_get_project():
    project = create_fake_project()

    with patch(
        "app.api.v1.projects.ProjectService.get_by_id",
        new=AsyncMock(return_value=project),
    ) as get_mock:
        response = client.get(f"/api/v1/projects/{project.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(project.id)
    assert data["organization_id"] == str(project.organization_id)
    assert data["name"] == project.name
    assert data["slug"] == project.slug

    get_mock.assert_awaited_once_with(project.id)


def test_get_project_returns_404_when_not_found():
    project_id = uuid4()

    with patch(
        "app.api.v1.projects.ProjectService.get_by_id",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        response = client.get(f"/api/v1/projects/{project_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

    get_mock.assert_awaited_once_with(project_id)


def test_list_projects():
    project_one = create_fake_project()
    project_two = create_fake_project()

    with patch(
        "app.api.v1.projects.ProjectService.list_by_organization",
        new=AsyncMock(return_value=[project_one, project_two]),
    ) as list_mock:
        response = client.get(f"/api/v1/projects?organization_id={project_one.organization_id}")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == str(project_one.id)
    assert data[1]["id"] == str(project_two.id)

    list_mock.assert_awaited_once_with(project_one.organization_id)


def test_update_project():
    project = create_fake_project()
    project.name = "Updated Project"

    with (
        patch(
            "app.api.v1.projects.ProjectService.get_by_id",
            new=AsyncMock(return_value=project),
        ) as get_mock,
        patch(
            "app.api.v1.projects.ProjectService.update",
            new=AsyncMock(return_value=project),
        ) as update_mock,
    ):
        response = client.patch(
            f"/api/v1/projects/{project.id}",
            json={"name": "Updated Project"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(project.id)
    assert data["name"] == "Updated Project"

    get_mock.assert_awaited_once_with(project.id)
    update_mock.assert_awaited_once()


def test_delete_project():
    project = create_fake_project()

    with (
        patch(
            "app.api.v1.projects.ProjectService.get_by_id",
            new=AsyncMock(return_value=project),
        ) as get_mock,
        patch(
            "app.api.v1.projects.ProjectService.delete",
            new=AsyncMock(),
        ) as delete_mock,
    ):
        response = client.delete(f"/api/v1/projects/{project.id}")

    assert response.status_code == 204
    assert response.content == b""

    get_mock.assert_awaited_once_with(project.id)
    delete_mock.assert_awaited_once_with(project)


def test_delete_project_returns_404_when_not_found():
    project_id = uuid4()

    with (
        patch(
            "app.api.v1.projects.ProjectService.get_by_id",
            new=AsyncMock(return_value=None),
        ) as get_mock,
        patch(
            "app.api.v1.projects.ProjectService.delete",
            new=AsyncMock(),
        ) as delete_mock,
    ):
        response = client.delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

    get_mock.assert_awaited_once_with(project_id)
    delete_mock.assert_not_awaited()


def test_delete_project_returns_409_when_active_datasets_exist():
    project = create_fake_project()

    with (
        patch(
            "app.api.v1.projects.ProjectService.get_by_id",
            new=AsyncMock(return_value=project),
        ) as get_mock,
        patch(
            "app.api.v1.projects.ProjectService.delete",
            new=AsyncMock(
                side_effect=ValueError("Cannot delete project because it has active datasets.")
            ),
        ) as delete_mock,
    ):
        response = client.delete(f"/api/v1/projects/{project.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == ("Cannot delete project because it has active datasets.")

    get_mock.assert_awaited_once_with(project.id)
    delete_mock.assert_awaited_once_with(project)
