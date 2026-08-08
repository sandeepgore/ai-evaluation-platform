from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_version.version import DatasetVersion
from app.schemas.dataset_version import (
    DatasetVersionCreate,
    DatasetVersionUpdate,
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
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version.desc())
        )

        return list(result.scalars().all())

    async def get(
        self,
        version_id: UUID,
    ) -> DatasetVersion:
        result = await self.db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == version_id
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

    async def delete(
        self,
        version_id: UUID,
    ) -> None:
        version = await self.get(version_id)

        await self.db.delete(version)
        await self.db.commit()