from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_fake_organization():
    return SimpleNamespace(
        id=uuid4(),
        name="Test Organization",
        slug="test-organization",
        description="Test organization description",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_create_organization():
    organization = create_fake_organization()

    with patch(
        "app.api.v1.organizations.OrganizationService.create",
        new=AsyncMock(return_value=organization),
    ) as create_mock:
        response = client.post(
            "/api/v1/organizations",
            json={
                "name": organization.name,
                "slug": organization.slug,
                "description": organization.description,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == str(organization.id)
    assert data["name"] == organization.name
    assert data["slug"] == organization.slug
    assert data["description"] == organization.description
    assert data["is_active"] is True

    create_mock.assert_awaited_once()


def test_create_organization_rejects_empty_name():
    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "",
            "slug": "test-organization",
        },
    )

    assert response.status_code == 422


def test_get_organization():
    organization = create_fake_organization()

    with patch(
        "app.api.v1.organizations.OrganizationService.get_by_id",
        new=AsyncMock(return_value=organization),
    ) as get_mock:
        response = client.get(f"/api/v1/organizations/{organization.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(organization.id)
    assert data["name"] == organization.name
    assert data["slug"] == organization.slug
    assert data["description"] == organization.description
    assert data["is_active"] is True

    get_mock.assert_awaited_once_with(organization.id)


def test_get_organization_returns_404_when_not_found():
    organization_id = uuid4()

    with patch(
        "app.api.v1.organizations.OrganizationService.get_by_id",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        response = client.get(f"/api/v1/organizations/{organization_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found"

    get_mock.assert_awaited_once_with(organization_id)


def test_list_organizations():
    organization_one = create_fake_organization()
    organization_two = create_fake_organization()

    with patch(
        "app.api.v1.organizations.OrganizationService.list_all",
        new=AsyncMock(return_value=[organization_one, organization_two]),
    ) as list_mock:
        response = client.get("/api/v1/organizations")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == str(organization_one.id)
    assert data[1]["id"] == str(organization_two.id)

    list_mock.assert_awaited_once()


def test_update_organization():
    organization = create_fake_organization()
    organization.name = "Updated Organization"

    with (
        patch(
            "app.api.v1.organizations.OrganizationService.get_by_id",
            new=AsyncMock(return_value=organization),
        ) as get_mock,
        patch(
            "app.api.v1.organizations.OrganizationService.update",
            new=AsyncMock(return_value=organization),
        ) as update_mock,
    ):
        response = client.patch(
            f"/api/v1/organizations/{organization.id}",
            json={
                "name": "Updated Organization",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(organization.id)
    assert data["name"] == "Updated Organization"

    get_mock.assert_awaited_once_with(organization.id)
    update_mock.assert_awaited_once()


def test_delete_organization():
    organization = create_fake_organization()

    with (
        patch(
            "app.api.v1.organizations.OrganizationService.get_by_id",
            new=AsyncMock(return_value=organization),
        ) as get_mock,
        patch(
            "app.api.v1.organizations.OrganizationService.delete",
            new=AsyncMock(),
        ) as delete_mock,
    ):
        response = client.delete(f"/api/v1/organizations/{organization.id}")

    assert response.status_code == 204
    assert response.content == b""

    get_mock.assert_awaited_once_with(organization.id)
    delete_mock.assert_awaited_once_with(organization)


def test_delete_organization_returns_404_when_not_found():
    organization_id = uuid4()

    with (
        patch(
            "app.api.v1.organizations.OrganizationService.get_by_id",
            new=AsyncMock(return_value=None),
        ) as get_mock,
        patch(
            "app.api.v1.organizations.OrganizationService.delete",
            new=AsyncMock(),
        ) as delete_mock,
    ):
        response = client.delete(f"/api/v1/organizations/{organization_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found"

    get_mock.assert_awaited_once_with(organization_id)
    delete_mock.assert_not_awaited()
