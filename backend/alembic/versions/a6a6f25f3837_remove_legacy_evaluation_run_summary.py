"""remove legacy evaluation run summary

Revision ID: a6a6f25f3837
Revises: 59bb4067f154
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6a6f25f3837"
down_revision: Union[str, Sequence[str], None] = "59bb4067f154"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column(
        "evaluation_runs",
        "summary",
    )


def downgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "summary",
            sa.JSON(),
            nullable=True,
        ),
    )
