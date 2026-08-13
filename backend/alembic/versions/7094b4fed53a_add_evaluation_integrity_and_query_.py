"""add evaluation integrity and query indexes

Revision ID: 7094b4fed53a
Revises: 65070b0d0d77
Create Date: 2026-08-13 21:47:02.181893

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7094b4fed53a"
down_revision: Union[str, Sequence[str], None] = "65070b0d0d77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_evaluation_results_run_case",
        "evaluation_results",
        ["evaluation_run_id", "dataset_case_id"],
        unique=True,
    )

    op.create_index(
        "uq_dataset_cases_version_position",
        "dataset_cases",
        ["dataset_version_id", "position"],
        unique=True,
    )

    op.create_index(
        "ix_evaluation_results_run_created_at",
        "evaluation_results",
        ["evaluation_run_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evaluation_results_run_created_at",
        table_name="evaluation_results",
    )

    op.drop_index(
        "uq_dataset_cases_version_position",
        table_name="dataset_cases",
    )

    op.drop_index(
        "uq_evaluation_results_run_case",
        table_name="evaluation_results",
    )
