"""add global roles to users"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ef20f4c6a891"
down_revision: Union[str, Sequence[str], None] = "d7c41b802e19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=20), server_default="user", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "role")
