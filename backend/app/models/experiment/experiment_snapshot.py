import uuid

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class ExperimentSnapshot(TimestampMixin, Base):
    __tablename__ = "experiment_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    run_ids: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    run_results: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    comparison: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    calculation_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
