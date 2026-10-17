"""add mode to evaluation schedules

Revision ID: bc21d4e7a19f
Revises: ea26f31a9365
Create Date: 2026-10-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bc21d4e7a19f"
down_revision: Union[str, Sequence[str], None] = "ea26f31a9365"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_schedules",
        sa.Column(
            "mode",
            sa.String(length=20),
            nullable=False,
            server_default="default",
        ),
    )
    op.alter_column("evaluation_schedules", "mode", server_default=None)


def downgrade() -> None:
    op.drop_column("evaluation_schedules", "mode")
