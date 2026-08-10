from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.evaluation import EvaluationRunStatus
from types import SimpleNamespace

client = TestClient(app)


def create_fake_run():
    return SimpleNamespace(
        id=uuid4(),
        dataset_version_id=uuid4(),
        model_id=uuid4(),
        name="API Test Evaluation",
        status=EvaluationRunStatus.PENDING,
        configuration={
            "evaluators": ["exact_match", "f1"],
            "scoring": {
                "strategy": "weighted",
                "weights": {
                    "exact_match": 0.5,
                    "f1": 0.5,
                },
            },
        },
        summary_feedback=None,
        total_cases=1,
        completed_cases=0,
        failed_cases=0,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

def test_create_evaluation_run():
    run = create_fake_run()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.create",
        new=AsyncMock(return_value=run),
    ):
        response = client.post(
            "/api/v1/evaluation-runs",
            json={
                "dataset_version_id": str(run.dataset_version_id),
                "model_id": str(run.model_id),
                "name": "API Test Evaluation",
                "configuration": {
                    "evaluators": ["exact_match", "f1"],
                    "scoring": {
                        "strategy": "weighted",
                        "weights": {
                            "exact_match": 0.5,
                            "f1": 0.5,
                        },
                    },
                },
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == str(run.id)
    assert data["name"] == "API Test Evaluation"
    assert data["status"] == run.status.value
    assert data["total_cases"] == 1


def test_get_evaluation_run():
    run = create_fake_run()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
        new=AsyncMock(return_value=run),
    ):
        response = client.get(
            f"/api/v1/evaluation-runs/{run.id}"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(run.id)
    assert data["name"] == run.name


def test_get_evaluation_run_returns_404_when_missing():
    run_id = uuid4()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
        new=AsyncMock(return_value=None),
    ):
        response = client.get(
            f"/api/v1/evaluation-runs/{run_id}"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Evaluation run not found"


def test_list_evaluation_runs():
    run = create_fake_run()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.list",
        new=AsyncMock(return_value=[run]),
    ):
        response = client.get(
            "/api/v1/evaluation-runs"
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(run.id)


def test_update_evaluation_run():
    run = create_fake_run()

    updated_run = create_fake_run()
    updated_run.id = run.id
    updated_run.name = "Updated Evaluation"

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
        new=AsyncMock(return_value=run),
    ), patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.update",
        new=AsyncMock(return_value=updated_run),
    ):
        response = client.patch(
            f"/api/v1/evaluation-runs/{run.id}",
            json={
                "name": "Updated Evaluation",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(run.id)
    assert data["name"] == "Updated Evaluation"


def test_delete_evaluation_run():
    run = create_fake_run()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
        new=AsyncMock(return_value=run),
    ), patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.delete",
        new=AsyncMock(),
    ) as delete_mock:
        response = client.delete(
            f"/api/v1/evaluation-runs/{run.id}"
        )

    assert response.status_code == 204
    delete_mock.assert_awaited_once()


def test_execute_evaluation_run():
    run = create_fake_run()

    completed_run = create_fake_run()
    completed_run.id = run.id
    completed_run.status = EvaluationRunStatus.COMPLETED
    completed_run.completed_cases = 1

    mock_engine = MagicMock()
    mock_engine.execute = AsyncMock(return_value=completed_run)

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationEngine",
        return_value=mock_engine,
    ):
        response = client.post(
            f"/api/v1/evaluation-runs/{run.id}/execute"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(run.id)
    assert data["status"] == EvaluationRunStatus.COMPLETED.value
    assert data["completed_cases"] == 1

    mock_engine.execute.assert_awaited_once_with(run.id)


def test_get_evaluation_run_summary():
    run_id = uuid4()

    summary = {
        "overall_score": 0.75,
        "metrics": {
            "exact_match": 0.5,
            "f1": 1.0,
        },
        "total_results": 2,
        "completed_cases": 2,
        "failed_cases": 0,
    }

    with patch(
        "app.api.v1.evaluation.evaluation."
        "EvaluationRunSummaryService.calculate",
        new=AsyncMock(return_value=summary),
    ):
        response = client.get(
            f"/api/v1/evaluation-runs/{run_id}/summary"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["overall_score"] == 0.75
    assert data["metrics"]["exact_match"] == 0.5
    assert data["metrics"]["f1"] == 1.0
    assert data["total_results"] == 2
    assert data["completed_cases"] == 2
    assert data["failed_cases"] == 0