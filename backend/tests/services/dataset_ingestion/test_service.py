from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.dataset_version.version import DatasetVersionStatus
from app.schemas.dataset_ingestion.dataset_import import (
    DatasetImportCase,
    DatasetImportPayload,
)
from app.services.dataset_ingestion.service import DatasetImportService


def build_dataset_lookup_result(dataset):
    result = MagicMock()
    result.scalar_one_or_none.return_value = dataset
    return result


def build_version_lookup_result(version_number):
    result = MagicMock()
    result.scalar_one.return_value = version_number
    return result


def build_db(dataset, next_version):
    db = AsyncMock()

    db.add = MagicMock()

    dataset_result = build_dataset_lookup_result(dataset)
    version_result = build_version_lookup_result(next_version)

    # First execute:
    #   SELECT dataset ... FOR UPDATE
    #
    # Second execute:
    #   SELECT MAX(version) + 1
    #
    # Third execute:
    #   INSERT dataset cases
    db.execute.side_effect = [
        dataset_result,
        version_result,
        MagicMock(),
    ]

    return db


@pytest.mark.asyncio
async def test_import_json_creates_ready_dataset_version_and_cases():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    db = build_db(
        dataset=dataset,
        next_version=1,
    )

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="What is AI?",
                expected_output="Artificial Intelligence",
                metadata={
                    "category": "ai",
                    "difficulty": "easy",
                },
            ),
            DatasetImportCase(
                input="What is ML?",
                expected_output="Machine Learning",
                metadata={
                    "category": "ml",
                    "difficulty": "medium",
                },
            ),
        ]
    )

    service = DatasetImportService(db)

    with patch("app.services.dataset_ingestion.service.insert") as mock_insert:
        version = await service.import_json(
            dataset_id,
            payload,
        )

    assert version.dataset_id == dataset_id
    assert version.version == 1
    assert version.status == DatasetVersionStatus.READY
    assert version.case_count == 2

    assert version.analytics is not None
    assert version.analytics["case_count"] == 2
    assert version.analytics["reference_count"] == 2
    assert version.analytics["context_count"] == 0
    assert version.analytics["reference_coverage"] == 1.0
    assert version.analytics["context_coverage"] == 0.0

    db.add.assert_called_once_with(version)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(version)

    mock_insert.assert_called_once()

    insert_execute_call = db.execute.await_args_list[2]

    inserted_rows = insert_execute_call.args[1]

    assert len(inserted_rows) == 2

    assert inserted_rows[0]["input"] == "What is AI?"
    assert inserted_rows[1]["input"] == "What is ML?"

    assert inserted_rows[0]["expected_output"] == ("Artificial Intelligence")
    assert inserted_rows[1]["expected_output"] == ("Machine Learning")
    assert inserted_rows[0]["case_metadata"] == {
        "category": "ai",
        "difficulty": "easy",
    }

    assert inserted_rows[1]["case_metadata"] == {
        "category": "ml",
        "difficulty": "medium",
    }
    assert inserted_rows[0]["has_reference"] is True
    assert inserted_rows[1]["has_reference"] is True

    assert [row["position"] for row in inserted_rows] == [0, 1]

    assert all(row["dataset_version_id"] == version.id for row in inserted_rows)


@pytest.mark.asyncio
async def test_import_json_creates_next_version_number():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    # IMPORTANT:
    # The service query is MAX(version) + 1.
    # Therefore scalar_one() represents the FINAL next version.
    db = build_db(
        dataset=dataset,
        next_version=5,
    )

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Test input",
                expected_output="Test output",
            )
        ]
    )

    service = DatasetImportService(db)

    with patch("app.services.dataset_ingestion.service.insert"):
        version = await service.import_json(
            dataset_id,
            payload,
        )

    assert version.version == 5
    assert version.dataset_id == dataset_id
    assert version.status == DatasetVersionStatus.READY


@pytest.mark.asyncio
async def test_import_json_assigns_sequential_case_positions():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    db = build_db(
        dataset=dataset,
        next_version=1,
    )

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Input 1",
                expected_output="Output 1",
            ),
            DatasetImportCase(
                input="Input 2",
                expected_output="Output 2",
            ),
            DatasetImportCase(
                input="Input 3",
                expected_output=None,
            ),
        ]
    )

    service = DatasetImportService(db)

    with patch("app.services.dataset_ingestion.service.insert") as mock_insert:
        version = await service.import_json(
            dataset_id,
            payload,
        )

    mock_insert.assert_called_once()

    insert_execute_call = db.execute.await_args_list[2]

    inserted_rows = insert_execute_call.args[1]

    assert len(inserted_rows) == 3

    assert [row["position"] for row in inserted_rows] == [
        0,
        1,
        2,
    ]

    assert [row["input"] for row in inserted_rows] == [
        "Input 1",
        "Input 2",
        "Input 3",
    ]

    assert [row["expected_output"] for row in inserted_rows] == [
        "Output 1",
        "Output 2",
        None,
    ]

    assert inserted_rows[0]["has_reference"] is True
    assert inserted_rows[1]["has_reference"] is True
    assert inserted_rows[2]["has_reference"] is False

    assert version.case_count == 3


@pytest.mark.asyncio
async def test_import_json_calculates_reference_coverage():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    db = build_db(
        dataset=dataset,
        next_version=1,
    )

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Input 1",
                expected_output="Output 1",
            ),
            DatasetImportCase(
                input="Input 2",
                expected_output=None,
            ),
            DatasetImportCase(
                input="Input 3",
                expected_output="Output 3",
            ),
            DatasetImportCase(
                input="Input 4",
                expected_output=None,
            ),
        ]
    )

    service = DatasetImportService(db)

    with patch("app.services.dataset_ingestion.service.insert"):
        version = await service.import_json(
            dataset_id,
            payload,
        )

    assert version.analytics is not None

    assert version.analytics["case_count"] == 4
    assert version.analytics["reference_count"] == 2
    assert version.analytics["reference_coverage"] == 0.5

    assert version.analytics["context_count"] == 0
    assert version.analytics["context_coverage"] == 0.0

    assert version.case_count == 4


@pytest.mark.asyncio
async def test_import_json_raises_404_when_dataset_not_found():
    dataset_result = MagicMock()
    dataset_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = dataset_result

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Test input",
            )
        ]
    )

    service = DatasetImportService(db)

    with pytest.raises(
        HTTPException,
        match="Dataset not found.",
    ):
        await service.import_json(
            uuid4(),
            payload,
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_import_json_rolls_back_on_integrity_error():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    dataset_result = build_dataset_lookup_result(dataset)
    version_result = build_version_lookup_result(1)

    integrity_error = IntegrityError(
        "statement",
        {},
        Exception("constraint violation"),
    )

    db = AsyncMock()
    db.add = MagicMock()

    # The IntegrityError occurs during DatasetCase insert.
    db.execute.side_effect = [
        dataset_result,
        version_result,
        integrity_error,
    ]

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Test input",
                expected_output="Test output",
            )
        ]
    )

    service = DatasetImportService(db)

    with pytest.raises(
        HTTPException,
        match=("Unable to import dataset because of a conflicting version or case."),
    ):
        await service.import_json(
            dataset_id,
            payload,
        )

    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_json_rolls_back_on_unexpected_error():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    dataset_result = build_dataset_lookup_result(dataset)
    version_result = build_version_lookup_result(1)

    db = AsyncMock()
    db.add = MagicMock()

    # The unexpected error occurs during DatasetCase insert.
    db.execute.side_effect = [
        dataset_result,
        version_result,
        RuntimeError("database failure"),
    ]

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Test input",
            )
        ]
    )

    service = DatasetImportService(db)

    with pytest.raises(
        RuntimeError,
        match="database failure",
    ):
        await service.import_json(
            dataset_id,
            payload,
        )

    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_json_calculates_context_capability():
    dataset_id = uuid4()

    dataset = MagicMock()
    dataset.id = dataset_id

    db = build_db(
        dataset=dataset,
        next_version=1,
    )

    payload = DatasetImportPayload(
        cases=[
            DatasetImportCase(
                input="Input 1",
                metadata={
                    "context": "Primary context",
                },
            ),
            DatasetImportCase(
                input="Input 2",
                metadata={
                    "retrieved_context": "Retrieved context",
                },
            ),
            DatasetImportCase(
                input="Input 3",
                metadata={
                    "reference_context": [
                        "Context one",
                        "Context two",
                    ],
                },
            ),
            DatasetImportCase(
                input="Input 4",
                metadata={
                    "category": "general",
                },
            ),
        ]
    )

    service = DatasetImportService(db)

    with patch("app.services.dataset_ingestion.service.insert") as mock_insert:
        version = await service.import_json(
            dataset_id,
            payload,
        )

    mock_insert.assert_called_once()

    insert_execute_call = db.execute.await_args_list[2]
    inserted_rows = insert_execute_call.args[1]

    assert len(inserted_rows) == 4

    assert [row["has_context"] for row in inserted_rows] == [
        True,
        True,
        True,
        False,
    ]

    assert version.analytics is not None
    assert version.analytics["context_count"] == 3
    assert version.analytics["context_coverage"] == 0.75
