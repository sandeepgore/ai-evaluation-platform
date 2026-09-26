import pytest
from pydantic import ValidationError

from app.schemas.organization.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)


def test_organization_create_accepts_valid_data():
    organization = OrganizationCreate(
        name="Test Organization",
        slug="test-organization",
        description="Test description",
    )

    assert organization.name == "Test Organization"
    assert organization.slug == "test-organization"
    assert organization.description == "Test description"


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", ""),
        ("slug", ""),
    ],
)
def test_organization_create_rejects_empty_strings(field, value):
    data = {
        "name": "Test Organization",
        "slug": "test-organization",
    }

    data[field] = value

    with pytest.raises(ValidationError):
        OrganizationCreate(**data)


def test_organization_create_rejects_name_longer_than_150_characters():
    with pytest.raises(ValidationError):
        OrganizationCreate(
            name="a" * 151,
            slug="test-organization",
        )


def test_organization_create_rejects_slug_longer_than_100_characters():
    with pytest.raises(ValidationError):
        OrganizationCreate(
            name="Test Organization",
            slug="a" * 101,
        )


def test_organization_update_allows_partial_update():
    data = OrganizationUpdate(
        name="Updated Organization",
    )

    assert data.name == "Updated Organization"
    assert data.slug is None
    assert data.description is None
    assert data.is_active is None


def test_organization_update_rejects_empty_name():
    with pytest.raises(ValidationError):
        OrganizationUpdate(name="")


def test_organization_update_rejects_empty_slug():
    with pytest.raises(ValidationError):
        OrganizationUpdate(slug="")
