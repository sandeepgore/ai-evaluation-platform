"""create evaluation summaries table

Revision ID: 59bb4067f154
Revises: f871c0d4d2d3
Create Date: 2026-08-28 13:56:51.858651
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "59bb4067f154"
down_revision: Union[str, Sequence[str], None] = "f871c0d4d2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_summaries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "evaluation_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "overall_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "metrics",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "performance",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "feedback",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"],
            ["evaluation_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evaluation_run_id",
            name="uq_evaluation_summaries_evaluation_run_id",
        ),
    )

    op.create_index(
        "ix_evaluation_summaries_evaluation_run_id",
        "evaluation_summaries",
        ["evaluation_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evaluation_summaries_evaluation_run_id",
        table_name="evaluation_summaries",
    )

    op.drop_table("evaluation_summaries")
