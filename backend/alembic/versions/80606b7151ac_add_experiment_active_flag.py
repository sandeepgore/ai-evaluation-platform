"""add experiment active flag

Revision ID: 80606b7151ac
Revises: 47c62afc7049
Create Date: 2026-09-25 18:06:44.203506

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "80606b7151ac"
down_revision: Union[str, Sequence[str], None] = "47c62afc7049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove obsolete legacy field.
    op.drop_column("evaluation_runs", "summary_feedback")

    # Add experiment lifecycle flag.
    # server_default safely initializes existing rows to True.
    op.add_column(
        "experiments",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    # Remove experiment lifecycle flag.
    op.drop_column("experiments", "is_active")

    # Restore obsolete legacy field.
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "summary_feedback",
            sa.Text(),
            nullable=True,
        ),
    )
