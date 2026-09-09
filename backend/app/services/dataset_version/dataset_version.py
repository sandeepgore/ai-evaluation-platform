from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_case.case import DatasetCase
from app.models.dataset_version.version import DatasetVersion, DatasetVersionStatus
from app.schemas.dataset_version import (
    DatasetVersionCreate,
    DatasetVersionUpdate,
)
from app.services.dataset_ingestion.analytics import (
    DatasetAnalyticsAccumulator,
)


class DatasetVersionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: DatasetVersionCreate,
    ) -> DatasetVersion:
        version = DatasetVersion(**data.model_dump())

        self.db.add(version)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This version already exists for this dataset.",
            )

        await self.db.refresh(version)

        return version

    async def list(
        self,
        dataset_id: UUID,
    ) -> list[DatasetVersion]:
        result = await self.db.execute(
            select(DatasetVersion)
            .where(
                DatasetVersion.dataset_id == dataset_id,
                DatasetVersion.is_active.is_(True),
            )
            .order_by(DatasetVersion.version.desc())
        )

        return list(result.scalars().all())

    async def get(
        self,
        version_id: UUID,
    ) -> DatasetVersion:
        result = await self.db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == version_id,
                DatasetVersion.is_active.is_(True),
            )
        )

        version = result.scalar_one_or_none()

        if version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset version not found.",
            )

        return version

    async def update(
        self,
        version_id: UUID,
        data: DatasetVersionUpdate,
    ) -> DatasetVersion:
        version = await self.get(version_id)

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(version, field, value)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to update dataset version.",
            )

        await self.db.refresh(version)

        return version

    async def finalize(
        self,
        version_id: UUID,
    ) -> DatasetVersion:
        version_result = await self.db.execute(
            select(DatasetVersion)
            .where(
                DatasetVersion.id == version_id,
                DatasetVersion.is_active.is_(True),
            )
            .with_for_update()
        )

        version = version_result.scalar_one_or_none()

        if version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset version not found.",
            )

        if version.status != DatasetVersionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only draft dataset versions can be finalized.",
            )

        cases_result = await self.db.execute(
            select(
                DatasetCase.has_reference,
                DatasetCase.has_context,
            ).where(
                DatasetCase.dataset_version_id == version_id,
                DatasetCase.is_active.is_(True),
            )
        )

        analytics = DatasetAnalyticsAccumulator()

        for has_reference, has_context in cases_result.all():
            analytics.observe(
                has_reference=has_reference,
                has_context=has_context,
            )

        analytics_data = analytics.to_dict()

        version.case_count = analytics_data["case_count"]
        version.analytics = analytics_data
        version.status = DatasetVersionStatus.READY

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        await self.db.refresh(version)

        return version

    async def delete(
        self,
        version_id: UUID,
    ) -> None:
        version = await self.get(version_id)

        version.is_active = False

        await self.db.commit()
