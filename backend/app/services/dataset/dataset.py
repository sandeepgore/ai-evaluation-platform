from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset.dataset import Dataset
from app.schemas.dataset.dataset import DatasetCreate, DatasetUpdate


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: DatasetCreate) -> Dataset:
        dataset = Dataset(
            project_id=data.project_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            dataset_type=data.dataset_type,
        )

        self.db.add(dataset)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("A dataset with this slug already exists in this project.")

        await self.db.refresh(dataset)

        return dataset

    async def get(self, dataset_id: UUID) -> Dataset | None:
        result = await self.db.execute(
            select(Dataset).where(
                Dataset.id == dataset_id,
                Dataset.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> list[Dataset]:
        result = await self.db.execute(
            select(Dataset)
            .where(
                Dataset.project_id == project_id,
                Dataset.is_active.is_(True),
            )
            .order_by(Dataset.created_at.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        dataset_id: UUID,
        data: DatasetUpdate,
    ) -> Dataset | None:
        dataset = await self.get(dataset_id)

        if dataset is None:
            return None

        if not dataset.is_active:
            raise ValueError("Cannot update an inactive dataset.")

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(dataset, field, value)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("A dataset with this slug already exists in this project.")

        await self.db.refresh(dataset)

        return dataset

    async def delete(self, dataset_id: UUID) -> bool:
        dataset = await self.get(dataset_id)

        if dataset is None:
            return False

        dataset.is_active = False
        await self.db.commit()

        return True
