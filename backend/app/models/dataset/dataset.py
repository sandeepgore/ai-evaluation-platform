import uuid
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class DatasetType(str, Enum):
    GENERATION = "generation"
    CLASSIFICATION = "classification"
    RAG = "rag"
    CONVERSATION = "conversation"
    CUSTOM = "custom"


class Dataset(TimestampMixin, Base):
    __tablename__ = "datasets"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "slug",
            name="uq_dataset_project_slug",
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

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    dataset_type: Mapped[DatasetType] = mapped_column(
        String(30),
        nullable=False,
        default=DatasetType.CUSTOM,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )