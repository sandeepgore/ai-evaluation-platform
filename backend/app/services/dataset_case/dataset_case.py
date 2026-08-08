from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_case import DatasetCase
from app.models.dataset_version import DatasetVersion
from app.schemas.dataset_case import DatasetCaseCreate, DatasetCaseUpdate


class DatasetCaseService:

    @staticmethod
    async def create(
        db: AsyncSession,
        data: DatasetCaseCreate,
    ) -> DatasetCase:
        version_result = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == data.dataset_version_id
            )
        )

        version = version_result.scalar_one_or_none()

        if version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset version not found.",
            )

        case = DatasetCase(
            dataset_version_id=data.dataset_version_id,
            input=data.input,
            expected_output=data.expected_output,
            case_metadata=data.case_metadata,
            position=data.position,
        )

        db.add(case)

        version.case_count += 1

        await db.commit()
        await db.refresh(case)

        return case

    @staticmethod
    async def list(
        db: AsyncSession,
        dataset_version_id: UUID,
    ) -> list[DatasetCase]:
        result = await db.execute(
            select(DatasetCase)
            .where(
                DatasetCase.dataset_version_id == dataset_version_id
            )
            .order_by(DatasetCase.position.asc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def get(
        db: AsyncSession,
        case_id: UUID,
    ) -> DatasetCase:
        result = await db.execute(
            select(DatasetCase).where(
                DatasetCase.id == case_id
            )
        )

        case = result.scalar_one_or_none()

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset case not found.",
            )

        return case

    @staticmethod
    async def update(
        db: AsyncSession,
        case_id: UUID,
        data: DatasetCaseUpdate,
    ) -> DatasetCase:
        case = await DatasetCaseService.get(db, case_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(case, field, value)

        await db.commit()
        await db.refresh(case)

        return case

    @staticmethod
    async def delete(
        db: AsyncSession,
        case_id: UUID,
    ) -> None:
        case = await DatasetCaseService.get(db, case_id)

        version_result = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == case.dataset_version_id
            )
        )

        version = version_result.scalar_one_or_none()

        if version is not None and version.case_count > 0:
            version.case_count -= 1

        await db.delete(case)

        await db.commit()