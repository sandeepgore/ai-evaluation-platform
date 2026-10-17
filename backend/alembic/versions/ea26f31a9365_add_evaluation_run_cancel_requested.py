"""add evaluation run cancel requested

Revision ID: ea26f31a9365
Revises: a35be8a6df96
Create Date: 2026-10-11 22:37:17.307411

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ea26f31a9365"
down_revision: Union[str, Sequence[str], None] = "a35be8a6df96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "cancel_requested",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.alter_column(
        "evaluation_runs",
        "cancel_requested",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "evaluation_runs",
        "cancel_requested",
    )
