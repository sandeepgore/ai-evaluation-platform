from functools import lru_cache

from app.shared.enums import DataPolicy
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    app_name: str = "AI Evaluation Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_evaluation"

    redis_url: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    dataset_insert_batch_size: int = 2_000
    model_gateway_timeout: int = 60

    # ------------------------------------------------------------------
    # Evaluation defaults
    # ------------------------------------------------------------------

    default_data_policy: DataPolicy = DataPolicy.STRICT
    default_data_policy_threshold: float = 1.0

    # ------------------------------------------------------------------
    # Prompt guardrails
    # ------------------------------------------------------------------

    # Maximum size of a configured prompt before variable rendering.
    max_prompt_size: int = 10_000

    # Maximum size of the final prompt sent to the model.
    max_rendered_prompt_size: int = 20_000

    # ------------------------------------------------------------------
    # Settings configuration
    # ------------------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
