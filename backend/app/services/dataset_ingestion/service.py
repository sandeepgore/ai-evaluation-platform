from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.dataset.dataset import Dataset
from app.models.dataset_case import DatasetCase
from app.models.dataset_version import DatasetVersion
from app.models.dataset_version.version import DatasetVersionStatus
from app.schemas.dataset_ingestion.dataset_import import DatasetImportPayload

from .analytics import DatasetAnalyticsAccumulator


class DatasetImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_json(
        self,
        dataset_id: UUID,
        payload: DatasetImportPayload,
    ) -> DatasetVersion:
        try:
            # Lock the dataset so concurrent imports for the same
            # dataset cannot select the same next version number.
            dataset_result = await self.db.execute(
                select(Dataset)
                .where(
                    Dataset.id == dataset_id,
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

            # Determine the next version number while the dataset row
            # is locked.
            version_result = await self.db.execute(
                select(
                    func.coalesce(
                        func.max(DatasetVersion.version),
                        0,
                    )
                    + 1
                ).where(
                    DatasetVersion.dataset_id == dataset_id,
                    DatasetVersion.is_active.is_(True),
                )
            )

            next_version = version_result.scalar_one()

            version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset_id,
                version=next_version,
                status=DatasetVersionStatus.DRAFT,
                case_count=0,
                analytics=None,
                is_active=True,
            )

            self.db.add(version)

            analytics = DatasetAnalyticsAccumulator()

            batch: list[dict] = []

            for position, imported_case in enumerate(payload.cases):
                has_reference = imported_case.expected_output is not None

                has_context = False

                if isinstance(imported_case.metadata, dict):
                    for key in (
                        "context",
                        "retrieved_context",
                        "reference_context",
                    ):
                        value = imported_case.metadata.get(key)

                        if isinstance(value, str):
                            if value.strip():
                                has_context = True
                                break

                        elif isinstance(value, (list, tuple)):
                            if any(isinstance(item, str) and item.strip() for item in value):
                                has_context = True
                                break

                analytics.observe(
                    has_reference=has_reference,
                    has_context=has_context,
                )

                batch.append(
                    {
                        "id": uuid4(),
                        "dataset_version_id": version.id,
                        "input": imported_case.input,
                        "expected_output": imported_case.expected_output,
                        "case_metadata": imported_case.metadata,
                        "has_reference": has_reference,
                        "has_context": has_context,
                        "position": position,
                        "is_active": True,
                    }
                )

                if len(batch) >= settings.dataset_insert_batch_size:
                    await self.db.execute(
                        insert(DatasetCase),
                        batch,
                    )
                    batch.clear()

            # Insert remaining cases.
            if batch:
                await self.db.execute(
                    insert(DatasetCase),
                    batch,
                )

            analytics_data = analytics.to_dict()

            version.case_count = analytics.case_count
            version.analytics = analytics_data
            version.status = DatasetVersionStatus.READY

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
                detail="Unable to import dataset because of a conflicting version or case.",
            )

        except Exception:
            await self.db.rollback()
            raise
