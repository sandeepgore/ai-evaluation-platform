import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class DatasetCase(TimestampMixin, Base):
    __tablename__ = "dataset_cases"

    __table_args__ = (
        Index(
            "uq_dataset_cases_version_position",
            "dataset_version_id",
            "position",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    input: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expected_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    case_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
