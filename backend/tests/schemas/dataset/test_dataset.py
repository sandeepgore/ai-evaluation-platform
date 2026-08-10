from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.dataset.dataset import DatasetType
from app.schemas.dataset.dataset import DatasetCreate, DatasetUpdate


def test_dataset_create_accepts_valid_data():
    project_id = uuid4()

    data = DatasetCreate(
        project_id=project_id,
        name="Test Dataset",
        slug="test-dataset",
        description="Test description",
        dataset_type=DatasetType.RAG,
    )

    assert data.project_id == project_id
    assert data.name == "Test Dataset"
    assert data.slug == "test-dataset"
    assert data.description == "Test description"
    assert data.dataset_type == DatasetType.RAG


def test_dataset_create_uses_custom_as_default_type():
    data = DatasetCreate(
        project_id=uuid4(),
        name="Test Dataset",
        slug="test-dataset",
    )

    assert data.dataset_type == DatasetType.CUSTOM


@pytest.mark.parametrize(
    "field",
    ["name", "slug"],
)
def test_dataset_create_rejects_empty_strings(field):
    with pytest.raises(ValidationError):
        DatasetCreate(
            project_id=uuid4(),
            name="" if field == "name" else "Test Dataset",
            slug="" if field == "slug" else "test-dataset",
        )


def test_dataset_create_rejects_name_longer_than_150_characters():
    with pytest.raises(ValidationError):
        DatasetCreate(
            project_id=uuid4(),
            name="a" * 151,
            slug="test-dataset",
        )


def test_dataset_create_rejects_slug_longer_than_100_characters():
    with pytest.raises(ValidationError):
        DatasetCreate(
            project_id=uuid4(),
            name="Test Dataset",
            slug="a" * 101,
        )


def test_dataset_create_rejects_invalid_project_id():
    with pytest.raises(ValidationError):
        DatasetCreate(
            project_id="not-a-uuid",
            name="Test Dataset",
            slug="test-dataset",
        )


def test_dataset_update_allows_partial_update():
    data = DatasetUpdate(
        name="Updated Dataset",
        description="Updated description",
    )

    assert data.name == "Updated Dataset"
    assert data.description == "Updated description"
    assert data.slug is None
    assert data.dataset_type is None
    assert data.is_active is None


@pytest.mark.parametrize(
    "field",
    ["name", "slug"],
)
def test_dataset_update_rejects_empty_strings(field):
    with pytest.raises(ValidationError):
        DatasetUpdate(
            name="" if field == "name" else None,
            slug="" if field == "slug" else None,
        )


def test_dataset_update_allows_is_active():
    data = DatasetUpdate(is_active=False)

    assert data.is_active is False


def test_dataset_update_allows_dataset_type():
    data = DatasetUpdate(dataset_type=DatasetType.GENERATION)

    assert data.dataset_type == DatasetType.GENERATION
