from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization.organization import Organization
from app.schemas.organization.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: OrganizationCreate,
    ) -> Organization:
        organization = Organization(
            name=data.name,
            slug=data.slug,
            description=data.description,
        )

        self.db.add(organization)
        await self.db.commit()
        await self.db.refresh(organization)

        return organization

    async def get_by_id(
        self,
        organization_id: UUID,
    ) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(
                Organization.id == organization_id,
                Organization.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    async def list_all(self) -> list[Organization]:
        result = await self.db.execute(
            select(Organization)
            .where(Organization.is_active.is_(True))
            .order_by(Organization.created_at.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        organization: Organization,
        data: OrganizationUpdate,
    ) -> Organization:
        if not organization.is_active:
            raise ValueError("Cannot update an inactive organization.")

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(organization, field, value)

        await self.db.commit()
        await self.db.refresh(organization)

        return organization

    async def delete(
        self,
        organization: Organization,
    ) -> None:
        organization.is_active = False

        await self.db.commit()
