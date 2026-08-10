from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_fake_result():
    return SimpleNamespace(
        id=uuid4(),
        evaluation_run_id=uuid4(),
        dataset_case_id=uuid4(),
        status="completed",
        actual_output="RAG combines retrieval and generation.",
        expected_output="RAG combines retrieval and generation.",
        scores={
            "exact_match": {"score": 1.0},
            "f1": {"score": 0.9},
            "overall": {"score": 0.95},
        },
        feedback="Good answer.",
        trace={},
        latency_ms=120,
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        error_message=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_get_evaluation_result():
    result = create_fake_result()

    with patch(
        "app.api.v1.evaluation_results.result.EvaluationResultService.get_by_id",
        new=AsyncMock(return_value=result),
    ):
        response = client.get(f"/api/v1/evaluation-results/{result.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(result.id)
    assert data["status"] == "completed"
    assert data["actual_output"] == result.actual_output
    assert data["scores"]["overall"]["score"] == 0.95


def test_get_evaluation_result_returns_404():
    result_id = uuid4()

    with patch(
        "app.api.v1.evaluation_results.result.EvaluationResultService.get_by_id",
        new=AsyncMock(return_value=None),
    ):
        response = client.get(f"/api/v1/evaluation-results/{result_id}")

    assert response.status_code == 404


def test_list_evaluation_results():
    result = create_fake_result()

    from app.schemas.evaluation_results import (
        EvaluationResultListResponse,
        EvaluationResultResponse,
    )

    response_data = EvaluationResultListResponse(
        items=[EvaluationResultResponse.model_validate(result)],
        total=1,
    )

    with patch(
        "app.api.v1.evaluation_results.result.EvaluationResultService.list_by_run",
        new=AsyncMock(return_value=response_data),
    ) as list_mock:
        response = client.get(
            "/api/v1/evaluation-results",
            params={
                "evaluation_run_id": str(result.evaluation_run_id),
                "status": "completed",
                "offset": 0,
                "limit": 50,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    list_mock.assert_awaited_once()


def test_get_evaluation_run_statistics():
    run_id = uuid4()

    statistics = {
        "total": 10,
        "completed": 8,
        "failed": 1,
        "pending": 1,
    }

    with patch(
        "app.api.v1.evaluation_results.result.EvaluationResultService.get_run_statistics",
        new=AsyncMock(return_value=statistics),
    ):
        response = client.get(f"/api/v1/evaluation-results/run/{run_id}/statistics")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 10
    assert data["completed"] == 8
    assert data["failed"] == 1
    assert data["pending"] == 1
