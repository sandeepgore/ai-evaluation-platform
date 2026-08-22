from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_case.case import DatasetCase
from app.models.dataset_version import DatasetVersion

from app.services.evaluation.dataset_capability import (
    DatasetCapabilities,
    DatasetCapabilityAnalyzer,
)


class DatasetCapabilityService:
    """
    DB-backed service for analyzing the capabilities of a dataset version.

    Responsibilities:
        - Verify that the dataset version exists.
        - Load active dataset cases from the database.
        - Delegate capability analysis to DatasetCapabilityAnalyzer.

    This service owns database access.
    DatasetCapabilityAnalyzer remains pure business logic.
    """

    @staticmethod
    async def analyze_dataset_version(
        db: AsyncSession,
        dataset_version_id: UUID,
    ) -> DatasetCapabilities:
        """
        Analyze the capabilities of a dataset version using
        the actual DatasetCase records stored in PostgreSQL.

        Only active dataset cases are considered.
        """

        # 1. Verify dataset version exists.
        version_result = await db.execute(
            select(DatasetVersion).where(DatasetVersion.id == dataset_version_id)
        )

        version = version_result.scalar_one_or_none()

        if version is None:
            raise ValueError(f"Dataset version not found: {dataset_version_id}")

        # 2. Load active dataset cases.
        cases_result = await db.execute(
            select(DatasetCase)
            .where(
                DatasetCase.dataset_version_id == dataset_version_id,
                DatasetCase.is_active.is_(True),
            )
            .order_by(DatasetCase.position.asc())
        )

        cases = list(cases_result.scalars().all())

        # 3. Delegate actual capability analysis.
        return DatasetCapabilityAnalyzer.analyze(cases)
