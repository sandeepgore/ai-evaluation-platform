import uuid
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class ModelProvider(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"
    CUSTOM = "custom"


class ModelType(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    RERANKER = "reranker"
    CUSTOM = "custom"


class Model(TimestampMixin, Base):
    __tablename__ = "models"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "provider",
            "model_identifier",
            name="uq_model_project_provider_identifier",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    provider: Mapped[ModelProvider] = mapped_column(
        String(30),
        nullable=False,
    )

    model_identifier: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    model_type: Mapped[ModelType] = mapped_column(
        String(30),
        nullable=False,
        default=ModelType.CHAT,
    )

    configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
