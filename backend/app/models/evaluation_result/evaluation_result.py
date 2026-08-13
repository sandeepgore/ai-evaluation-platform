import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class EvaluationResult(TimestampMixin, Base):
    __tablename__ = "evaluation_results"

    __table_args__ = (
        Index(
            "uq_evaluation_results_run_case",
            "evaluation_run_id",
            "dataset_case_id",
            unique=True,
        ),
        Index(
            "ix_evaluation_results_run_created_at",
            "evaluation_run_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dataset_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dataset_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    actual_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expected_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    scores: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    trace: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
