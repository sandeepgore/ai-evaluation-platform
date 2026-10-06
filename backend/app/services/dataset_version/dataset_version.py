from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset.dataset import Dataset
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
        try:
            dataset_result = await self.db.execute(
                select(Dataset)
                .where(
                    Dataset.id == data.dataset_id,
                    Dataset.is_active.is_(True),
                )
                .with_for_update()
            )

            dataset = dataset_result.scalar_one_or_none()

            if dataset is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found.",
                )

            version_result = await self.db.execute(
                select(
                    func.coalesce(
                        func.max(DatasetVersion.version),
                        0,
                    )
                    + 1
                ).where(
                    DatasetVersion.dataset_id == data.dataset_id,
                )
            )

            next_version = version_result.scalar_one()

            version = DatasetVersion(
                dataset_id=data.dataset_id,
                version=next_version,
                status=DatasetVersionStatus.DRAFT,
                description=data.description,
                case_count=0,
                analytics=None,
                is_active=True,
            )

            self.db.add(version)

            await self.db.commit()
            await self.db.refresh(version)

            return version

        except HTTPException:
            await self.db.rollback()
            raise

        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This version already exists for this dataset.",
            )

        except Exception:
            await self.db.rollback()
            raise

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

        case_result = await self.db.execute(
            select(DatasetCase.id)
            .where(
                DatasetCase.dataset_version_id == version_id,
                DatasetCase.is_active.is_(True),
            )
            .limit(1)
        )

        if case_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete a dataset version that has cases.",
            )

        version.is_active = False

        await self.db.commit()
