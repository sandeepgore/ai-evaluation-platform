from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.project.project import ProjectCreate, ProjectUpdate
from app.services.project.project import ProjectService


@pytest.mark.asyncio
async def test_create_project():
    db = AsyncMock()
    db.add = MagicMock()

    data = ProjectCreate(
        organization_id=uuid4(),
        name="Test Project",
        slug="test-project",
        description="Test project description",
    )

    service = ProjectService(db)

    project = await service.create(data)

    assert project.organization_id == data.organization_id
    assert project.name == data.name
    assert project.slug == data.slug
    assert project.description == data.description

    db.add.assert_called_once_with(project)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(project)


@pytest.mark.asyncio
async def test_get_by_id_returns_project():
    project = MagicMock()
    project.id = uuid4()

    result = MagicMock()
    result.scalar_one_or_none.return_value = project

    db = AsyncMock()
    db.execute.return_value = result

    service = ProjectService(db)

    returned = await service.get_by_id(project.id)

    assert returned == project

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_project_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    service = ProjectService(db)

    project_id = uuid4()

    returned = await service.get_by_id(project_id)

    assert returned is None

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_by_organization():
    organization_id = uuid4()

    project_one = MagicMock()
    project_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        project_one,
        project_two,
    ]

    db = AsyncMock()
    db.execute.return_value = result

    service = ProjectService(db)

    projects = await service.list_by_organization(organization_id)

    assert projects == [project_one, project_two]

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_project():
    project = MagicMock()
    project.name = "Old Name"
    project.slug = "old-name"
    project.description = "Old description"

    db = AsyncMock()

    data = ProjectUpdate(
        name="Updated Project",
        description="Updated description",
    )

    service = ProjectService(db)

    updated = await service.update(project, data)

    assert updated == project
    assert project.name == "Updated Project"
    assert project.slug == "old-name"
    assert project.description == "Updated description"

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(project)


@pytest.mark.asyncio
async def test_update_project_with_no_fields():
    project = MagicMock()

    db = AsyncMock()

    data = ProjectUpdate()

    service = ProjectService(db)

    updated = await service.update(project, data)

    assert updated == project

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(project)


@pytest.mark.asyncio
async def test_delete_project():
    project = MagicMock()

    db = AsyncMock()

    service = ProjectService(db)

    await service.delete(project)

    db.delete.assert_awaited_once_with(project)
    db.commit.assert_awaited_once()
