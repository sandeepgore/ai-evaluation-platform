from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project.project import Project
from app.schemas.project.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ProjectCreate) -> Project:
        project = Project(
            organization_id=data.organization_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def get_by_id(self, project_id: UUID) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )

        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        project: Project,
        data: ProjectUpdate,
    ) -> Project:
        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.commit()