import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.models.model import ModelProvider, ModelType
from app.schemas.model import ModelCreate, ModelUpdate


def test_model_create_accepts_valid_data():
    project_id = uuid4()

    data = ModelCreate(
        project_id=project_id,
        name="GPT Mock",
        provider=ModelProvider.MOCK,
        model_identifier="mock-model",
        model_type=ModelType.CHAT,
        configuration={"temperature": 0.7},
    )

    assert data.project_id == project_id
    assert data.name == "GPT Mock"
    assert data.provider == ModelProvider.MOCK
    assert data.model_identifier == "mock-model"
    assert data.model_type == ModelType.CHAT
    assert data.configuration == {"temperature": 0.7}


def test_model_create_uses_chat_as_default_type():
    data = ModelCreate(
        project_id=uuid4(),
        name="Test Model",
        provider=ModelProvider.MOCK,
        model_identifier="test-model",
    )

    assert data.model_type == ModelType.CHAT


@pytest.mark.parametrize("field", ["name", "model_identifier"])
def test_model_create_rejects_empty_strings(field):
    payload = {
        "project_id": uuid4(),
        "name": "Test Model",
        "provider": ModelProvider.MOCK,
        "model_identifier": "test-model",
    }

    payload[field] = ""

    with pytest.raises(ValidationError):
        ModelCreate(**payload)


def test_model_create_rejects_name_longer_than_150_characters():
    with pytest.raises(ValidationError):
        ModelCreate(
            project_id=uuid4(),
            name="a" * 151,
            provider=ModelProvider.MOCK,
            model_identifier="test-model",
        )


def test_model_create_rejects_identifier_longer_than_150_characters():
    with pytest.raises(ValidationError):
        ModelCreate(
            project_id=uuid4(),
            name="Test Model",
            provider=ModelProvider.MOCK,
            model_identifier="a" * 151,
        )


def test_model_create_rejects_invalid_project_id():
    with pytest.raises(ValidationError):
        ModelCreate(
            project_id="not-a-uuid",
            name="Test Model",
            provider=ModelProvider.MOCK,
            model_identifier="test-model",
        )


@pytest.mark.parametrize("provider", list(ModelProvider))
def test_model_create_accepts_all_supported_providers(provider):
    data = ModelCreate(
        project_id=uuid4(),
        name="Test Model",
        provider=provider,
        model_identifier="test-model",
    )

    assert data.provider == provider


@pytest.mark.parametrize("model_type", list(ModelType))
def test_model_create_accepts_all_supported_model_types(model_type):
    data = ModelCreate(
        project_id=uuid4(),
        name="Test Model",
        provider=ModelProvider.MOCK,
        model_identifier="test-model",
        model_type=model_type,
    )

    assert data.model_type == model_type


def test_model_update_allows_partial_update():
    data = ModelUpdate(
        name="Updated Model",
        is_active=False,
    )

    assert data.name == "Updated Model"
    assert data.is_active is False
    assert data.provider is None
    assert data.model_identifier is None
    assert data.model_type is None


@pytest.mark.parametrize("field", ["name", "model_identifier"])
def test_model_update_rejects_empty_strings(field):
    with pytest.raises(ValidationError):
        ModelUpdate(**{field: ""})


def test_model_update_allows_configuration():
    data = ModelUpdate(
        configuration={
            "temperature": 0.2,
            "max_tokens": 500,
        }
    )

    assert data.configuration == {
        "temperature": 0.2,
        "max_tokens": 500,
    }


def test_model_update_allows_is_active():
    data = ModelUpdate(is_active=False)

    assert data.is_active is False


def test_model_update_allows_provider_and_type():
    data = ModelUpdate(
        provider=ModelProvider.OPENAI,
        model_type=ModelType.COMPLETION,
    )

    assert data.provider == ModelProvider.OPENAI
    assert data.model_type == ModelType.COMPLETION
