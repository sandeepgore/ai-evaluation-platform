import pytest

from app.config.settings import Settings


def test_settings_loads_without_provider_credentials():
    settings = Settings()

    assert settings.openai_api_key is None
    assert settings.anthropic_api_key is None
    assert settings.google_api_key is None


@pytest.mark.parametrize(
    ("env_name", "field_name", "api_key"),
    [
        ("OPENAI_API_KEY", "openai_api_key", "test-openai-key"),
        ("ANTHROPIC_API_KEY", "anthropic_api_key", "test-anthropic-key"),
        ("GOOGLE_API_KEY", "google_api_key", "test-google-key"),
    ],
)
def test_provider_api_keys_load_from_environment(
    monkeypatch,
    env_name,
    field_name,
    api_key,
):
    monkeypatch.setenv(env_name, api_key)

    settings = Settings()

    assert getattr(settings, field_name) == api_key


def test_provider_credentials_are_optional(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    settings = Settings()

    assert settings.openai_api_key is None
    assert settings.anthropic_api_key is None
    assert settings.google_api_key is None


def test_existing_settings_still_load():
    settings = Settings()

    assert settings.database_url
    assert settings.redis_url
    assert settings.model_gateway_timeout == 60
    assert settings.default_data_policy_threshold == 1.0
