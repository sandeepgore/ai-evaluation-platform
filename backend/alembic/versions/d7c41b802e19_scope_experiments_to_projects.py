"""scope experiments to projects

Revision ID: d7c41b802e19
Revises: bc21d4e7a19f
Create Date: 2026-10-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7c41b802e19"
down_revision: Union[str, Sequence[str], None] = "bc21d4e7a19f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "experiments",
        sa.Column("project_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_experiments_project_id_projects",
        "experiments",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_experiments_project_id",
        "experiments",
        ["project_id"],
    )
    op.execute(
        """
        UPDATE experiments AS experiment
        SET project_id = (
            SELECT MIN(dataset.project_id::text)::uuid
            FROM experiment_snapshots AS snapshot
            CROSS JOIN LATERAL jsonb_array_elements_text(snapshot.run_ids) AS run_id(value)
            JOIN evaluation_runs AS run ON run.id = run_id.value::uuid
            JOIN dataset_versions AS version ON version.id = run.dataset_version_id
            JOIN datasets AS dataset ON dataset.id = version.dataset_id
            WHERE snapshot.experiment_id = experiment.id
            HAVING COUNT(DISTINCT dataset.project_id) = 1
        )
        WHERE EXISTS (
            SELECT 1 FROM experiment_snapshots AS snapshot
            WHERE snapshot.experiment_id = experiment.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_experiments_project_id", table_name="experiments")
    op.drop_constraint(
        "fk_experiments_project_id_projects",
        "experiments",
        type_="foreignkey",
    )
    op.drop_column("experiments", "project_id")
