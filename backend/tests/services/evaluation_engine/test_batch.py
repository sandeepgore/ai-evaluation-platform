from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_type import EvaluationType
from app.schemas.model_gateway import ModelResponse
from app.schemas.model_gateway.batch_response import BatchModelResponse
from app.services.evaluation_engine import engine as engine_module
from app.services.evaluation_engine.engine import EvaluationEngine
from tests.services.evaluation_engine.test_engine import (
    FakeRegistry,
    capabilities_from_cases,
)


def mock_run_summary_services(
    monkeypatch,
):
    monkeypatch.setattr(
        engine_module.EvaluationRunSummaryService,
        "calculate",
        AsyncMock(
            return_value={
                "model": None,
                "overall_score": 0.0,
                "metrics": {},
                "total_results": 0,
                "completed_cases": 0,
                "failed_cases": 0,
                "feedback": {
                    "overall": "Test summary.",
                    "strengths": [],
                    "weaknesses": [],
                    "patterns": [],
                    "recommendations": [],
                    "evaluator_feedback": [],
                },
                "performance": {},
            }
        ),
    )

    monkeypatch.setattr(
        engine_module.EvaluationSummaryPersistenceService,
        "save",
        AsyncMock(
            return_value=SimpleNamespace(),
        ),
    )


@pytest.mark.asyncio
async def test_engine_handles_batch_inference_failure_and_continues(
    monkeypatch,
):
    """
    When one batch fails during model inference:

    - every case in the failed batch is marked failed
    - subsequent batches continue executing
    - successful batches are marked completed
    - the final run contains correct counters

    20 cases are processed in batches of 5.
    The first batch fails.
    """

    run_id = uuid4()
    model_id = uuid4()
    dataset_version_id = uuid4()

    cases = [
        SimpleNamespace(
            id=uuid4(),
            input=f"Question {index}",
            expected_output=f"Answer {index}",
            has_reference=True,
            has_context=False,
        )
        for index in range(1, 21)
    ]

    run = SimpleNamespace(
        id=run_id,
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        evaluation_type=EvaluationType.TEXT,
        configuration={
            "execution_mode": "batch",
            "batch_size": 5,
            "batch_concurrency": 3,
            "evaluators": [
                {
                    "name": "exact_match",
                    "weight": 0.5,
                },
                {
                    "name": "f1",
                    "weight": 0.5,
                },
            ],
            "scoring": {
                "weights": {
                    "exact_match": 0.5,
                    "f1": 0.5,
                }
            },
        },
        status=EvaluationRunStatus.PENDING,
        total_cases=0,
        completed_cases=0,
        failed_cases=0,
    )

    model = SimpleNamespace(
        id=model_id,
        name="Mock Model",
        provider="mock",
        model_identifier="mock-model",
        configuration={},
        is_active=True,
    )

    db = MagicMock()

    result = MagicMock()

    result.scalar_one_or_none.return_value = model
    result.scalars.return_value.all.return_value = []

    db.execute = AsyncMock(
        return_value=result,
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()

    def successful_response(index: int) -> ModelResponse:
        return ModelResponse(
            output=f"Answer {index}",
            trace={},
            latency_ms=10,
            input_tokens=2,
            output_tokens=2,
            total_tokens=4,
        )

    def successful_batch(
        start_index: int,
        end_index: int,
    ) -> list[BatchModelResponse]:
        return [
            BatchModelResponse(
                index=index - start_index,
                response=successful_response(index),
                error=None,
            )
            for index in range(
                start_index,
                end_index + 1,
            )
        ]

    model_gateway.generate_batch = AsyncMock(
        side_effect=[
            RuntimeError("Simulated batch inference failure"),
            successful_batch(6, 10),
            successful_batch(11, 15),
            successful_batch(16, 20),
        ]
    )

    scoring_service = MagicMock()

    scoring_service.calculate.return_value = SimpleNamespace(
        score=0.75,
        metadata={
            "strategy": "weighted",
        },
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=cases),
    )

    # Dataset-level capabilities are now read from persisted
    # DatasetVersion.analytics by the production engine.
    # This mock keeps the batch test focused on batch failure isolation.
    monkeypatch.setattr(
        engine_module.DatasetCapabilityService,
        "analyze_dataset_version",
        AsyncMock(
            return_value=capabilities_from_cases(cases),
        ),
    )

    evaluation_result_create = AsyncMock()

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    mock_run_summary_services(
        monkeypatch,
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=FakeRegistry(),
        scoring_service=scoring_service,
    )

    result = await engine.execute(run_id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 20
    assert result.completed_cases == 15
    assert result.failed_cases == 5

    assert model_gateway.generate_batch.await_count == 4

    model_gateway.generate.assert_not_awaited()

    assert evaluation_result_create.await_count == 20

    assert scoring_service.calculate.call_count == 15

    calls = model_gateway.generate_batch.await_args_list

    assert len(calls) == 4

    assert calls[0].kwargs["prompts"] == [
        "Question 1",
        "Question 2",
        "Question 3",
        "Question 4",
        "Question 5",
    ]

    assert calls[1].kwargs["prompts"] == [
        "Question 6",
        "Question 7",
        "Question 8",
        "Question 9",
        "Question 10",
    ]

    assert calls[2].kwargs["prompts"] == [
        "Question 11",
        "Question 12",
        "Question 13",
        "Question 14",
        "Question 15",
    ]

    assert calls[3].kwargs["prompts"] == [
        "Question 16",
        "Question 17",
        "Question 18",
        "Question 19",
        "Question 20",
    ]


@pytest.mark.asyncio
async def test_engine_isolates_individual_batch_item_failure(
    monkeypatch,
):
    """
    One item in a batch may fail while the other items succeed.

    The failed item must be persisted as failed while successful
    items continue through evaluation and scoring.
    """

    run_id = uuid4()
    model_id = uuid4()
    dataset_version_id = uuid4()

    cases = [
        SimpleNamespace(
            id=uuid4(),
            input=f"Question {index}",
            expected_output=f"Answer {index}",
            has_reference=True,
            has_context=False,
        )
        for index in range(1, 4)
    ]

    run = SimpleNamespace(
        id=run_id,
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        evaluation_type=EvaluationType.TEXT,
        configuration={
            "execution_mode": "batch",
            "batch_size": 3,
            "batch_concurrency": 3,
            "evaluators": [
                "exact_match",
            ],
        },
        status=EvaluationRunStatus.PENDING,
        total_cases=0,
        completed_cases=0,
        failed_cases=0,
    )

    model = SimpleNamespace(
        id=model_id,
        name="Mock Model",
        provider="mock",
        model_identifier="mock-model",
        configuration={},
        is_active=True,
    )

    db = MagicMock()

    result = MagicMock()

    result.scalar_one_or_none.return_value = model
    result.scalars.return_value.all.return_value = []

    db.execute = AsyncMock(
        return_value=result,
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    successful_response = ModelResponse(
        output="Answer",
        trace={},
        latency_ms=10,
        input_tokens=2,
        output_tokens=2,
        total_tokens=4,
    )

    model_gateway = MagicMock()

    model_gateway.generate_batch = AsyncMock(
        return_value=[
            BatchModelResponse(
                index=0,
                response=successful_response,
                error=None,
            ),
            BatchModelResponse(
                index=1,
                response=None,
                error={
                    "type": "ReadTimeout",
                    "message": "Simulated timeout",
                },
            ),
            BatchModelResponse(
                index=2,
                response=successful_response,
                error=None,
            ),
        ]
    )

    model_gateway.generate = AsyncMock()

    scoring_service = MagicMock()

    scoring_service.calculate.return_value = SimpleNamespace(
        score=1.0,
        metadata={
            "strategy": "weighted",
        },
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=cases),
    )

    # Dataset-level capabilities are now read from persisted
    # DatasetVersion.analytics by the production engine.
    # This mock keeps the test focused on individual batch-item failure.
    monkeypatch.setattr(
        engine_module.DatasetCapabilityService,
        "analyze_dataset_version",
        AsyncMock(
            return_value=capabilities_from_cases(cases),
        ),
    )

    evaluation_result_create = AsyncMock()

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    mock_run_summary_services(
        monkeypatch,
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=FakeRegistry(),
        scoring_service=scoring_service,
    )

    result = await engine.execute(run_id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 3
    assert result.completed_cases == 2
    assert result.failed_cases == 1

    model_gateway.generate_batch.assert_awaited_once()
    model_gateway.generate.assert_not_awaited()

    assert scoring_service.calculate.call_count == 2

    assert evaluation_result_create.await_count == 3

    failed_calls = [
        call
        for call in evaluation_result_create.await_args_list
        if call.kwargs["status"] == "failed"
    ]

    assert len(failed_calls) == 1

    failed_call = failed_calls[0]

    assert failed_call.kwargs["actual_output"] is None
    assert failed_call.kwargs["scores"] == {}
    assert "ReadTimeout" in failed_call.kwargs["error_message"]
