from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_version import DatasetVersion
from app.models.evaluation import EvaluationSchedule, EvaluationScheduleType
from app.models.model import Model
from app.schemas.evaluation import EvaluationScheduleCreate, EvaluationScheduleUpdate


class EvaluationScheduleService:
    @staticmethod
    async def create(
        db: AsyncSession,
        data: EvaluationScheduleCreate,
    ) -> EvaluationSchedule:
        # --------------------------------------------------------------
        # Verify dataset version exists
        # --------------------------------------------------------------

        dataset_version_result = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == data.dataset_version_id,
                DatasetVersion.is_active.is_(True),
            )
        )

        dataset_version = dataset_version_result.scalar_one_or_none()

        if dataset_version is None:
            raise ValueError("Dataset version not found")

        # --------------------------------------------------------------
        # Verify model exists
        # --------------------------------------------------------------

        model_result = await db.execute(
            select(Model).where(
                Model.id == data.model_id,
                Model.is_active.is_(True),
            )
        )

        model = model_result.scalar_one_or_none()

        if model is None:
            raise ValueError("Model not found")

        # --------------------------------------------------------------
        # Validate schedule
        # --------------------------------------------------------------

        next_run_at = data.next_run_at

        if data.schedule_type == EvaluationScheduleType.ONE_TIME:
            if next_run_at is None:
                raise ValueError("next_run_at is required for one-time schedules.")

            if next_run_at.tzinfo is None:
                raise ValueError("next_run_at must be timezone-aware.")

        if data.schedule_type == EvaluationScheduleType.RECURRING:
            try:
                schedule_timezone = ZoneInfo(data.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("Invalid timezone") from exc

            now_local = datetime.now(schedule_timezone)

            try:
                cron = croniter(data.schedule_expression, now_local)
                next_run_at = cron.get_next(datetime).astimezone(UTC)
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid schedule expression") from exc

        # --------------------------------------------------------------
        # Create schedule
        # --------------------------------------------------------------

        schedule = EvaluationSchedule(
            dataset_version_id=data.dataset_version_id,
            model_id=data.model_id,
            name=data.name,
            evaluation_type=data.evaluation_type,
            configuration=data.configuration,
            schedule_type=data.schedule_type,
            schedule_expression=data.schedule_expression,
            timezone=data.timezone,
            next_run_at=next_run_at,
            last_run_at=None,
            is_active=True,
        )

        db.add(schedule)

        await db.commit()
        await db.refresh(schedule)

        return schedule

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        schedule_id: UUID,
    ) -> EvaluationSchedule | None:
        result = await db.execute(
            select(EvaluationSchedule).where(
                EvaluationSchedule.id == schedule_id,
                EvaluationSchedule.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        dataset_version_id: UUID | None = None,
        model_id: UUID | None = None,
    ) -> list[EvaluationSchedule]:
        query = select(EvaluationSchedule).where(EvaluationSchedule.is_active.is_(True))

        if dataset_version_id is not None:
            query = query.where(EvaluationSchedule.dataset_version_id == dataset_version_id)

        if model_id is not None:
            query = query.where(EvaluationSchedule.model_id == model_id)

        query = query.order_by(EvaluationSchedule.created_at.desc())

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        schedule: EvaluationSchedule,
        data: EvaluationScheduleUpdate,
    ) -> EvaluationSchedule:
        if not schedule.is_active:
            raise ValueError("Evaluation schedule is inactive")

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(schedule, field, value)

        await db.commit()
        await db.refresh(schedule)

        return schedule

    @staticmethod
    async def delete(
        db: AsyncSession,
        schedule: EvaluationSchedule,
    ) -> None:
        if not schedule.is_active:
            raise ValueError("Evaluation schedule is already inactive")

        schedule.is_active = False
        await db.commit()

    @staticmethod
    async def claim_due(
        db: AsyncSession,
        *,
        limit: int = 10,
    ) -> list[EvaluationSchedule]:
        now = datetime.now(UTC)

        result = await db.execute(
            select(EvaluationSchedule)
            .where(
                EvaluationSchedule.is_active.is_(True),
                EvaluationSchedule.next_run_at.is_not(None),
                EvaluationSchedule.next_run_at <= now,
            )
            .order_by(EvaluationSchedule.next_run_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        return list(result.scalars().all())
