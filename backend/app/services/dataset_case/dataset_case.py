from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_case import DatasetCase
from app.models.dataset_version import (
    DatasetVersion,
    DatasetVersionStatus,
)
from app.schemas.dataset_case import (
    DatasetCaseCreate,
    DatasetCaseUpdate,
)
from app.services.dataset_case.capability import (
    derive_case_capabilities,
)


class DatasetCaseService:
    @staticmethod
    async def create(
        db: AsyncSession,
        data: DatasetCaseCreate,
    ) -> DatasetCase:
        try:
            # Lock the dataset version row so concurrent case creation
            # requests for the same version are serialized.
            version_result = await db.execute(
                select(DatasetVersion)
                .where(
                    DatasetVersion.id == data.dataset_version_id,
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

            # Cases can only be added while the dataset version
            # is being manually constructed.
            if version.status != DatasetVersionStatus.DRAFT:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Dataset cases can only be added to draft dataset versions.",
                )

            # Position is backend-controlled.
            #
            # We intentionally do not use case_count here because
            # deleted cases can leave gaps in positions.
            position_result = await db.execute(
                select(func.coalesce(func.max(DatasetCase.position), -1) + 1).where(
                    DatasetCase.dataset_version_id == data.dataset_version_id,
                    DatasetCase.is_active.is_(True),
                )
            )

            position = position_result.scalar_one()

            # Derive case-level capabilities from the actual case data.
            has_reference, has_context = derive_case_capabilities(
                expected_output=data.expected_output,
                case_metadata=data.case_metadata,
            )

            case = DatasetCase(
                dataset_version_id=data.dataset_version_id,
                input=data.input,
                expected_output=data.expected_output,
                case_metadata=data.case_metadata,
                has_reference=has_reference,
                has_context=has_context,
                position=position,
            )

            db.add(case)

            version.case_count += 1

            await db.commit()
            await db.refresh(case)

            return case

        except HTTPException:
            await db.rollback()
            raise

        except IntegrityError:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to create dataset case due to a conflicting position.",
            )

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def list(
        db: AsyncSession,
        dataset_version_id: UUID,
    ) -> list[DatasetCase]:
        result = await db.execute(
            select(DatasetCase)
            .where(
                DatasetCase.dataset_version_id == dataset_version_id,
                DatasetCase.is_active.is_(True),
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
                DatasetCase.id == case_id,
                DatasetCase.is_active.is_(True),
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
        try:
            case = await DatasetCaseService.get(
                db,
                case_id,
            )

            if not case.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset case not found.",
                )

            # Lock the parent dataset version so case mutations
            # are serialized against other lifecycle operations.
            version_result = await db.execute(
                select(DatasetVersion)
                .where(
                    DatasetVersion.id == case.dataset_version_id, DatasetVersion.is_active.is_(True)
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
                    detail=("Dataset cases can only be updated in draft dataset versions."),
                )

            update_data = data.model_dump(
                exclude_unset=True,
            )

            # Update the case fields first.
            for field, value in update_data.items():
                setattr(case, field, value)

            # Capability flags are derived from the current case state.
            #
            # Analytics are intentionally not recalculated here.
            # They are recalculated when the draft version is finalized.
            if "expected_output" in update_data or "case_metadata" in update_data:
                (
                    case.has_reference,
                    case.has_context,
                ) = derive_case_capabilities(
                    expected_output=case.expected_output,
                    case_metadata=case.case_metadata,
                )

            await db.commit()
            await db.refresh(case)

            return case

        except HTTPException:
            await db.rollback()
            raise

        except IntegrityError:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("Unable to update dataset case due to a conflicting position."),
            )

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete(
        db: AsyncSession,
        case_id: UUID,
    ) -> None:
        try:
            case = await DatasetCaseService.get(
                db,
                case_id,
            )

            if not case.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset case not found.",
                )

            version_result = await db.execute(
                select(DatasetVersion)
                .where(
                    DatasetVersion.id == case.dataset_version_id,
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
                    detail=("Dataset cases can only be deleted from draft dataset versions."),
                )

            if version.case_count > 0:
                version.case_count -= 1

            case.is_active = False

            await db.commit()

        except HTTPException:
            await db.rollback()
            raise

        except Exception:
            await db.rollback()
            raise
