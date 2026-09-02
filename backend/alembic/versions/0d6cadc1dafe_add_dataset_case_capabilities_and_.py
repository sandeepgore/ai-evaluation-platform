"""add dataset case capabilities and version analytics

Revision ID: 0d6cadc1dafe
Revises: a6a6f25f3837
Create Date: 2026-09-01 13:53:55.438813

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0d6cadc1dafe"
down_revision: Union[str, Sequence[str], None] = "a6a6f25f3837"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------------------
    # Dataset case capabilities
    #
    # Add as nullable first so existing rows can be backfilled safely.
    # --------------------------------------------------------------

    op.add_column(
        "dataset_cases",
        sa.Column(
            "has_reference",
            sa.Boolean(),
            nullable=True,
        ),
    )

    op.add_column(
        "dataset_cases",
        sa.Column(
            "has_context",
            sa.Boolean(),
            nullable=True,
        ),
    )

    # --------------------------------------------------------------
    # Dataset version analytics
    # --------------------------------------------------------------

    op.add_column(
        "dataset_versions",
        sa.Column(
            "analytics",
            sa.JSON(),
            nullable=True,
        ),
    )

    # --------------------------------------------------------------
    # Backfill has_reference
    # --------------------------------------------------------------

    op.execute(
        sa.text(
            """
            UPDATE dataset_cases
            SET has_reference = (
                expected_output IS NOT NULL
                AND btrim(expected_output) <> ''
            )
            """
        )
    )

    # --------------------------------------------------------------
    # Backfill has_context
    #
    # Supported metadata keys:
    #   context
    #   retrieved_context
    #   reference_context
    #
    # Supported values:
    #   non-empty string
    # --------------------------------------------------------------

    op.execute(
        sa.text(
            """
            UPDATE dataset_cases
            SET has_context = COALESCE(
                (
                    (
                        jsonb_typeof(metadata::jsonb -> 'context') = 'string'
                        AND btrim(metadata::jsonb ->> 'context') <> ''
                    )
                    OR
                    (
                        jsonb_typeof(
                            metadata::jsonb -> 'retrieved_context'
                        ) = 'string'
                        AND btrim(
                            metadata::jsonb ->> 'retrieved_context'
                        ) <> ''
                    )
                    OR
                    (
                        jsonb_typeof(
                            metadata::jsonb -> 'reference_context'
                        ) = 'string'
                        AND btrim(
                            metadata::jsonb ->> 'reference_context'
                        ) <> ''
                    )
                ),
                false
            )
            """
        )
    )

    # --------------------------------------------------------------
    # Enforce NOT NULL after backfill
    # --------------------------------------------------------------

    op.alter_column(
        "dataset_cases",
        "has_reference",
        nullable=False,
    )

    op.alter_column(
        "dataset_cases",
        "has_context",
        nullable=False,
    )


def downgrade() -> None:
    # --------------------------------------------------------------
    # Remove dataset version analytics
    # --------------------------------------------------------------

    op.drop_column(
        "dataset_versions",
        "analytics",
    )

    # --------------------------------------------------------------
    # Remove dataset case capabilities
    # --------------------------------------------------------------

    op.drop_column(
        "dataset_cases",
        "has_context",
    )

    op.drop_column(
        "dataset_cases",
        "has_reference",
    )
