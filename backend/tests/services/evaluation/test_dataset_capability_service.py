from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.evaluation.dataset_capability_service import (
    DatasetCapabilityService,
)


@pytest.mark.asyncio
async def test_analyze_dataset_version_reads_active_cases():
    dataset_version_id = uuid4()

    dataset_version = MagicMock()
    dataset_version.id = dataset_version_id

    case_one = MagicMock()
    case_one.position = 0
    case_one.is_active = True
    case_one.expected_output = "Paris"
    case_one.case_metadata = {"context": "Paris is the capital of France."}

    case_two = MagicMock()
    case_two.position = 1
    case_two.is_active = True
    case_two.expected_output = "London"
    case_two.case_metadata = {"context": "London is the capital of England."}

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    cases_result = MagicMock()
    cases_result.scalars.return_value.all.return_value = [
        case_one,
        case_two,
    ]

    db = AsyncMock()
    db.execute.side_effect = [
        version_result,
        cases_result,
    ]

    capabilities = await DatasetCapabilityService.analyze_dataset_version(
        db=db,
        dataset_version_id=dataset_version_id,
    )

    assert capabilities.total_cases == 2

    assert capabilities.cases_with_reference == 2
    assert capabilities.cases_without_reference == 0
    assert capabilities.reference_coverage == 1.0

    assert capabilities.cases_with_context == 2
    assert capabilities.cases_without_context == 0
    assert capabilities.context_coverage == 1.0

    assert capabilities.has_reference is True
    assert capabilities.has_context is True

    assert capabilities.all_cases_have_reference is True
    assert capabilities.all_cases_have_context is True

    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_analyze_dataset_version_handles_partial_capabilities():
    dataset_version_id = uuid4()

    dataset_version = MagicMock()
    dataset_version.id = dataset_version_id

    case_one = MagicMock()
    case_one.position = 0
    case_one.is_active = True
    case_one.expected_output = "Paris"
    case_one.case_metadata = {"context": "Paris is the capital of France."}

    case_two = MagicMock()
    case_two.position = 1
    case_two.is_active = True
    case_two.expected_output = None
    case_two.case_metadata = None

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    cases_result = MagicMock()
    cases_result.scalars.return_value.all.return_value = [
        case_one,
        case_two,
    ]

    db = AsyncMock()
    db.execute.side_effect = [
        version_result,
        cases_result,
    ]

    capabilities = await DatasetCapabilityService.analyze_dataset_version(
        db=db,
        dataset_version_id=dataset_version_id,
    )

    assert capabilities.total_cases == 2

    assert capabilities.cases_with_reference == 1
    assert capabilities.cases_without_reference == 1
    assert capabilities.reference_coverage == 0.5

    assert capabilities.cases_with_context == 1
    assert capabilities.cases_without_context == 1
    assert capabilities.context_coverage == 0.5

    assert capabilities.has_reference is True
    assert capabilities.has_context is True

    assert capabilities.all_cases_have_reference is False
    assert capabilities.all_cases_have_context is False


@pytest.mark.asyncio
async def test_analyze_dataset_version_returns_zero_capabilities_for_empty_dataset():
    dataset_version_id = uuid4()

    dataset_version = MagicMock()
    dataset_version.id = dataset_version_id

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = dataset_version

    cases_result = MagicMock()
    cases_result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute.side_effect = [
        version_result,
        cases_result,
    ]

    capabilities = await DatasetCapabilityService.analyze_dataset_version(
        db=db,
        dataset_version_id=dataset_version_id,
    )

    assert capabilities.total_cases == 0

    assert capabilities.has_reference is False
    assert capabilities.has_context is False

    assert capabilities.reference_coverage == 0.0
    assert capabilities.context_coverage == 0.0


@pytest.mark.asyncio
async def test_analyze_dataset_version_raises_when_dataset_version_not_found():
    dataset_version_id = uuid4()

    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = version_result

    with pytest.raises(
        ValueError,
        match="Dataset version not found",
    ):
        await DatasetCapabilityService.analyze_dataset_version(
            db=db,
            dataset_version_id=dataset_version_id,
        )

    # Since the version does not exist, the cases query must never run.
    db.execute.assert_awaited_once()
