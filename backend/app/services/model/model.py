from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model
from app.schemas.model import ModelCreate, ModelUpdate


class ModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ModelCreate) -> Model:
        model = Model(**data.model_dump())

        self.db.add(model)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A model with this provider and identifier already exists in this project.",
            )

        await self.db.refresh(model)
        return model

    async def get(self, model_id: UUID) -> Model:
        result = await self.db.execute(
            select(Model).where(Model.id == model_id)
        )

        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )

        return model

    async def list(self, project_id: UUID) -> list[Model]:
        result = await self.db.execute(
            select(Model)
            .where(Model.project_id == project_id)
            .order_by(Model.created_at.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        model_id: UUID,
        data: ModelUpdate,
    ) -> Model:
        model = await self.get(model_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(model, field, value)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A model with this provider and identifier already exists in this project.",
            )

        await self.db.refresh(model)
        return model

    async def delete(self, model_id: UUID) -> None:
        model = await self.get(model_id)

        await self.db.delete(model)
        await self.db.commit()