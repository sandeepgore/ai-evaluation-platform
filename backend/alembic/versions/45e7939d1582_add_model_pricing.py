"""add model pricing

Revision ID: 45e7939d1582
Revises: 619ee34233ea
Create Date: 2026-08-27 12:47:31.929784

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "45e7939d1582"
down_revision: Union[str, Sequence[str], None] = "619ee34233ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "models",
        sa.Column(
            "input_price_per_million",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "models",
        sa.Column(
            "output_price_per_million",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "models",
        sa.Column(
            "pricing_currency",
            sa.String(length=10),
            nullable=False,
            server_default="USD",
        ),
    )


def downgrade() -> None:
    op.drop_column("models", "pricing_currency")
    op.drop_column("models", "output_price_per_million")
    op.drop_column("models", "input_price_per_million")
