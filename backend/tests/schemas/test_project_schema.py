import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.schemas.project.project import ProjectCreate, ProjectUpdate


def test_project_create_accepts_valid_data():
    project = ProjectCreate(
        organization_id=uuid4(),
        name="Test Project",
        slug="test-project",
        description="Test description",
    )

    assert project.name == "Test Project"
    assert project.slug == "test-project"


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", ""),
        ("slug", ""),
    ],
)
def test_project_create_rejects_empty_strings(field, value):
    data = {
        "organization_id": uuid4(),
        "name": "Test Project",
        "slug": "test-project",
    }

    data[field] = value

    with pytest.raises(ValidationError):
        ProjectCreate(**data)


def test_project_create_rejects_name_longer_than_150_characters():
    with pytest.raises(ValidationError):
        ProjectCreate(
            organization_id=uuid4(),
            name="a" * 151,
            slug="test-project",
        )


def test_project_create_rejects_slug_longer_than_100_characters():
    with pytest.raises(ValidationError):
        ProjectCreate(
            organization_id=uuid4(),
            name="Test Project",
            slug="a" * 101,
        )


def test_project_create_rejects_invalid_organization_id():
    with pytest.raises(ValidationError):
        ProjectCreate(
            organization_id="not-a-uuid",
            name="Test Project",
            slug="test-project",
        )


def test_project_update_allows_partial_update():
    data = ProjectUpdate(
        name="Updated Project",
    )

    assert data.name == "Updated Project"
    assert data.slug is None
    assert data.description is None


def test_project_update_rejects_empty_name():
    with pytest.raises(ValidationError):
        ProjectUpdate(name="")


def test_project_update_rejects_empty_slug():
    with pytest.raises(ValidationError):
        ProjectUpdate(slug="")
