from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_version import DatasetVersion
from app.services.evaluation.dataset_capability import DatasetCapabilities


class DatasetCapabilityService:
    """
    DB-backed service for reading the capabilities of a dataset version.

    DatasetVersion.analytics is the persisted source of truth for
    dataset-level capability aggregates.

    DatasetCase.has_reference and DatasetCase.has_context remain the
    source of truth for case-level eligibility decisions.
    """

    @staticmethod
    async def analyze_dataset_version(
        db: AsyncSession,
        dataset_version_id: UUID,
    ) -> DatasetCapabilities:
        """
        Read persisted dataset capability aggregates from PostgreSQL.
        """

        result = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == dataset_version_id,
                DatasetVersion.is_active.is_(True),
            )
        )

        version = result.scalar_one_or_none()

        if version is None:
            raise ValueError(f"Dataset version not found: {dataset_version_id}")

        analytics = version.analytics or {}

        total_cases = int(analytics.get("case_count", 0))
        cases_with_reference = int(analytics.get("reference_count", 0))
        cases_with_context = int(analytics.get("context_count", 0))

        cases_without_reference = total_cases - cases_with_reference
        cases_without_context = total_cases - cases_with_context

        reference_coverage = float(analytics.get("reference_coverage", 0.0))
        context_coverage = float(analytics.get("context_coverage", 0.0))

        return DatasetCapabilities(
            total_cases=total_cases,
            cases_with_reference=cases_with_reference,
            cases_without_reference=cases_without_reference,
            cases_with_context=cases_with_context,
            cases_without_context=cases_without_context,
            has_reference=cases_with_reference > 0,
            has_context=cases_with_context > 0,
            all_cases_have_reference=(total_cases > 0 and cases_with_reference == total_cases),
            all_cases_have_context=(total_cases > 0 and cases_with_context == total_cases),
            reference_coverage=reference_coverage,
            context_coverage=context_coverage,
        )
