"""add evaluation run summary

Revision ID: f871c0d4d2d3
Revises: 45e7939d1582
Create Date: 2026-08-28 12:14:07.545552

"""

from typing import Sequence, Union

from alembic import op

import sqlalchemy as sa


revision: str = "f871c0d4d2d3"
down_revision: Union[str, Sequence[str], None] = "45e7939d1582"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "summary",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "evaluation_runs",
        "summary",
    )
