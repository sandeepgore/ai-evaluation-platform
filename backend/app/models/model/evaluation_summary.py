from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class EvaluationSummary(TimestampMixin, Base):
    """
    Persisted final summary for an evaluation run.

    PostgreSQL is the source of truth for the summary.
    Redis may cache the serialized summary for fast API reads.

    Deterministic data:
        - overall_score
        - metrics
        - performance

    Qualitative data:
        - feedback

    Metadata:
        - summary model/provider
        - generation information
        - future summary versioning
    """

    __tablename__ = "evaluation_summaries"

    __table_args__ = (
        UniqueConstraint(
            "evaluation_run_id",
            name="uq_evaluation_summaries_evaluation_run_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    evaluation_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    overall_score: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
    )

    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    performance: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    feedback: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    summary_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
