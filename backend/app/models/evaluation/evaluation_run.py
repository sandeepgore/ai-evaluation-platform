import uuid
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class EvaluationRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationRun(TimestampMixin, Base):
    __tablename__ = "evaluation_runs"

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

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[EvaluationRunStatus] = mapped_column(
        String(20),
        nullable=False,
        default=EvaluationRunStatus.PENDING,
    )

    configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    summary_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    total_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )