"""add evaluation type to evaluation runs

Revision ID: 619ee34233ea
Revises: 7094b4fed53a
Create Date: 2026-08-18 13:19:58.659200

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "619ee34233ea"
down_revision: Union[str, Sequence[str], None] = "7094b4fed53a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EVALUATION_TYPE = sa.Enum(
    "text",
    "rag",
    "conversation",
    "safety",
    name="evaluation_type",
    native_enum=False,
)


def upgrade() -> None:
    # --------------------------------------------------------------
    # 1. Add the column temporarily nullable so existing rows are safe.
    # --------------------------------------------------------------

    op.add_column(
        "evaluation_runs",
        sa.Column(
            "evaluation_type",
            EVALUATION_TYPE,
            nullable=True,
        ),
    )

    # --------------------------------------------------------------
    # 2. Backfill existing evaluation runs.
    #
    # Existing runs predate explicit evaluation types, so they are
    # treated as standard text evaluations.
    # --------------------------------------------------------------

    op.execute(
        """
        UPDATE evaluation_runs
        SET evaluation_type = 'text'
        WHERE evaluation_type IS NULL
        """
    )

    # --------------------------------------------------------------
    # 3. Enforce the new invariant.
    # --------------------------------------------------------------

    op.alter_column(
        "evaluation_runs",
        "evaluation_type",
        existing_type=EVALUATION_TYPE,
        nullable=False,
    )

    # --------------------------------------------------------------
    # 4. Add index for filtering/grouping by evaluation type.
    # --------------------------------------------------------------

    op.create_index(
        op.f("ix_evaluation_runs_evaluation_type"),
        "evaluation_runs",
        ["evaluation_type"],
        unique=False,
    )


def downgrade() -> None:
    # --------------------------------------------------------------
    # Remove index first, then column.
    # --------------------------------------------------------------

    op.drop_index(
        op.f("ix_evaluation_runs_evaluation_type"),
        table_name="evaluation_runs",
    )

    op.drop_column(
        "evaluation_runs",
        "evaluation_type",
    )
