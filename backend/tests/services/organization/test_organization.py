import uuid
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.organization.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)
from app.services.organization.organization import OrganizationService


@pytest.mark.asyncio
async def test_create_organization():
    db = AsyncMock()
    db.add = MagicMock()

    data = OrganizationCreate(
        name="Test Organization",
        slug="test-organization",
        description="Test organization description",
    )

    service = OrganizationService(db)

    organization = await service.create(data)

    assert organization.name == data.name
    assert organization.slug == data.slug
    assert organization.description == data.description

    db.add.assert_called_once_with(organization)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(organization)


@pytest.mark.asyncio
async def test_get_by_id_returns_organization():
    organization = MagicMock()
    organization.id = uuid4()

    result = MagicMock()
    result.scalar_one_or_none.return_value = organization

    db = AsyncMock()
    db.execute.return_value = result

    service = OrganizationService(db)

    returned = await service.get_by_id(organization.id)

    assert returned == organization
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = OrganizationService(db)

    organization = await service.get_by_id(uuid4())

    assert organization is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_all():
    organization_one = MagicMock()
    organization_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        organization_one,
        organization_two,
    ]

    db = AsyncMock()
    db.execute.return_value = result

    service = OrganizationService(db)

    organizations = await service.list_all()

    assert organizations == [
        organization_one,
        organization_two,
    ]

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_organization():
    organization = MagicMock()
    organization.name = "Old Name"
    organization.slug = "old-name"
    organization.description = "Old description"
    organization.is_active = True

    db = AsyncMock()

    data = OrganizationUpdate(
        name="Updated Organization",
        description="Updated description",
    )

    service = OrganizationService(db)

    updated = await service.update(organization, data)

    assert updated == organization
    assert organization.name == "Updated Organization"
    assert organization.slug == "old-name"
    assert organization.description == "Updated description"

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(organization)


@pytest.mark.asyncio
async def test_update_organization_with_no_fields():
    organization = MagicMock()
    organization.is_active = True

    db = AsyncMock()

    data = OrganizationUpdate()

    service = OrganizationService(db)

    updated = await service.update(organization, data)

    assert updated == organization
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(organization)


@pytest.mark.asyncio
async def test_delete_organization():
    organization = MagicMock()
    organization.is_active = True

    db = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    service = OrganizationService(db)

    await service.delete(organization)

    assert organization.is_active is False
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_organization_rejects_associated_projects():
    organization = MagicMock()
    organization.id = uuid.uuid4()
    organization.is_active = True

    db = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = uuid.uuid4()
    db.execute.return_value = result

    service = OrganizationService(db)

    with pytest.raises(
        ValueError,
        match="Cannot delete organization because it has associated projects.",
    ):
        await service.delete(organization)

    assert organization.is_active is True
    db.commit.assert_not_awaited()
