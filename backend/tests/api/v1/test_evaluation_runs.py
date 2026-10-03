import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.evaluation.run_validation import EvaluationRunValidationError
import pytest
from fastapi.testclient import TestClient

from app.db.redis import get_redis
from app.main import app
from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_type import EvaluationType

client = TestClient(app)


def create_fake_run():
    return SimpleNamespace(
        id=uuid4(),
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
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
        not_applicable_cases=0,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None,
        duration_ms=None,
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


def test_create_evaluation_run_returns_400_when_validation_fails():
    validation_error = EvaluationRunValidationError(
        {
            "message": "Evaluation run violates the selected data policy.",
            "policy": "strict",
            "requirement": "reference",
            "coverage": 0.5,
            "required_coverage": 1.0,
            "reason": "Strict policy requires complete reference coverage.",
        }
    )

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.create",
        new=AsyncMock(side_effect=validation_error),
    ) as create_mock:
        response = client.post(
            "/api/v1/evaluation-runs",
            json={
                "dataset_version_id": str(uuid4()),
                "model_id": str(uuid4()),
                "name": "Strict Policy Validation Test",
                "configuration": {
                    "evaluators": ["exact_match"],
                    "data_policy": {
                        "type": "strict",
                    },
                },
            },
        )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["message"] == ("Evaluation run violates the selected data policy.")
    assert detail["policy"] == "strict"
    assert detail["requirement"] == "reference"
    assert detail["coverage"] == 0.5
    assert detail["required_coverage"] == 1.0
    assert detail["reason"] == ("Strict policy requires complete reference coverage.")

    create_mock.assert_awaited_once()


def test_get_evaluation_run():
    run = create_fake_run()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
        new=AsyncMock(return_value=run),
    ):
        response = client.get(f"/api/v1/evaluation-runs/{run.id}")

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
        response = client.get(f"/api/v1/evaluation-runs/{run_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Evaluation run not found"


def test_list_evaluation_runs():
    run = create_fake_run()

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunService.list",
        new=AsyncMock(return_value=[run]),
    ):
        response = client.get("/api/v1/evaluation-runs")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(run.id)


def test_update_evaluation_run():
    run = create_fake_run()

    updated_run = create_fake_run()
    updated_run.id = run.id
    updated_run.name = "Updated Evaluation"

    with (
        patch(
            "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
            new=AsyncMock(return_value=run),
        ),
        patch(
            "app.api.v1.evaluation.evaluation.EvaluationRunService.update",
            new=AsyncMock(return_value=updated_run),
        ),
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

    with (
        patch(
            "app.api.v1.evaluation.evaluation.EvaluationRunService.get_by_id",
            new=AsyncMock(return_value=run),
        ),
        patch(
            "app.api.v1.evaluation.evaluation.EvaluationRunService.delete",
            new=AsyncMock(),
        ) as delete_mock,
    ):
        response = client.delete(f"/api/v1/evaluation-runs/{run.id}")

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
        response = client.post(f"/api/v1/evaluation-runs/{run.id}/execute")

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
        "feedback": {
            "overall": ("Moderate overall evaluation performance with some areas for improvement."),
            "strengths": [
                "High F1 indicates strong token-level similarity to reference answers.",
                "Responses generally preserve important answer content.",
                "Evaluation results show consistent performance across completed cases.",
            ],
            "weaknesses": [
                (
                    "Low exact-match performance indicates responses "
                    "frequently differ from expected answers."
                ),
                ("Some responses could align more precisely with the reference wording."),
                ("Variation across evaluation metrics indicates room for improvement."),
            ],
            "patterns": [
                ("Responses often preserve the main answer while differing in exact wording."),
                ("Token-level similarity is stronger than exact-match agreement."),
                (
                    "The evaluation shows a recurring gap between "
                    "semantic usefulness and exact reference alignment."
                ),
            ],
            "recommendations": [
                "Improve answer alignment with the expected reference responses.",
                (
                    "Preserve key information while reducing unnecessary "
                    "deviations from expected answers."
                ),
                ("Continue monitoring both exact-match and F1 performance across future runs."),
            ],
            "evaluator_feedback": [
                "f1: strong token overlap with reference answer",
            ],
        },
        "total_results": 2,
        "completed_cases": 2,
        "failed_cases": 0,
        "not_applicable_cases": 0,
        "performance": {
            "total_results": 2,
            "completed_cases": 2,
            "failed_cases": 0,
            "not_applicable_cases": 0,
            "duration_ms": 10000,
            "total_model_latency_ms": 6000,
            "avg_model_latency_ms": 3000.0,
            "min_model_latency_ms": 2000,
            "p50_model_latency_ms": 3000.0,
            "p95_model_latency_ms": 3900.0,
            "p99_model_latency_ms": 3980.0,
            "max_model_latency_ms": 4000,
            "input_tokens": 250,
            "output_tokens": 450,
            "total_tokens": 700,
            "throughput_cases_per_second": 0.2,
            "cost": {
                "input_cost": 0.001,
                "output_cost": 0.002,
                "total_cost": 0.003,
                "currency": "USD",
            },
        },
    }

    with patch(
        "app.api.v1.evaluation.evaluation.EvaluationRunSummaryService.calculate",
        new=AsyncMock(return_value=summary),
    ):
        response = client.get(f"/api/v1/evaluation-runs/{run_id}/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["overall_score"] == 0.75
    assert data["metrics"]["exact_match"] == 0.5
    assert data["metrics"]["f1"] == 1.0

    feedback = data["feedback"]

    assert (
        feedback["overall"]
        == "Moderate overall evaluation performance with some areas for improvement."
    )

    assert (
        "High F1 indicates strong token-level similarity to reference answers."
        in feedback["strengths"]
    )

    assert (
        "Low exact-match performance indicates responses frequently differ from expected answers."
        in feedback["weaknesses"]
    )

    assert (
        "Continue monitoring both exact-match and F1 performance across future runs."
        in feedback["recommendations"]
    )

    assert "f1: strong token overlap with reference answer" in feedback["evaluator_feedback"]

    assert data["total_results"] == 2
    assert data["completed_cases"] == 2
    assert data["failed_cases"] == 0
    assert data["not_applicable_cases"] == 0

    performance = data["performance"]

    assert performance["total_results"] == 2
    assert performance["completed_cases"] == 2
    assert performance["failed_cases"] == 0
    assert performance["not_applicable_cases"] == 0

    assert performance["duration_ms"] == 10000
    assert performance["total_model_latency_ms"] == 6000
    assert performance["avg_model_latency_ms"] == 3000.0
    assert performance["min_model_latency_ms"] == 2000
    assert performance["p50_model_latency_ms"] == 3000.0
    assert performance["p95_model_latency_ms"] == 3900.0
    assert performance["p99_model_latency_ms"] == 3980.0
    assert performance["max_model_latency_ms"] == 4000

    assert performance["input_tokens"] == 250
    assert performance["output_tokens"] == 450
    assert performance["total_tokens"] == 700
    assert performance["throughput_cases_per_second"] == 0.2

    assert performance["cost"]["input_cost"] == 0.001
    assert performance["cost"]["output_cost"] == 0.002
    assert performance["cost"]["total_cost"] == 0.003
    assert performance["cost"]["currency"] == "USD"


def test_get_evaluation_run_summary_cache_hit():
    run_id = uuid4()

    cached_summary = {
        "model": None,
        "overall_score": 0.85,
        "metrics": {
            "f1": 0.85,
        },
        "feedback": {
            "overall": "Strong overall evaluation performance.",
            "strengths": [
                "High F1 performance.",
                "Responses demonstrate strong answer alignment.",
                ("Completed evaluations show consistently strong metric performance."),
            ],
            "weaknesses": [
                "Some responses may still differ from the reference wording.",
                "Further improvement in exact alignment is possible.",
                "Minor metric variation may remain across evaluation cases.",
            ],
            "patterns": [
                ("Strong token-level similarity appears consistently across evaluated cases."),
                "Responses generally preserve expected answer content.",
                ("The evaluation shows stable performance across completed cases."),
            ],
            "recommendations": [
                "Maintain the current level of answer quality.",
                ("Continue monitoring metric consistency across future evaluation runs."),
                "Improve exact alignment where small differences remain.",
            ],
            "evaluator_feedback": [],
        },
        "total_results": 5,
        "completed_cases": 5,
        "failed_cases": 0,
        "not_applicable_cases": 0,
        "performance": {
            "total_results": 5,
            "completed_cases": 5,
            "failed_cases": 0,
            "not_applicable_cases": 0,
            "duration_ms": 10000,
            "total_model_latency_ms": 5000,
            "avg_model_latency_ms": 1000.0,
            "min_model_latency_ms": 500,
            "p50_model_latency_ms": 1000.0,
            "p95_model_latency_ms": 1500.0,
            "p99_model_latency_ms": 1500.0,
            "max_model_latency_ms": 2000,
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "throughput_cases_per_second": 0.5,
            "cost": {
                "input_cost": 0.001,
                "output_cost": 0.002,
                "total_cost": 0.003,
                "currency": "USD",
            },
        },
    }

    redis = MagicMock()
    redis.get = AsyncMock(return_value=json.dumps(cached_summary))
    redis.set = AsyncMock()

    app.dependency_overrides[get_redis] = lambda: redis

    try:
        with patch(
            "app.api.v1.evaluation.evaluation.EvaluationRunSummaryService.calculate",
            new=AsyncMock(),
        ) as calculate_mock:
            response = client.get(f"/api/v1/evaluation-runs/{run_id}/summary")

        assert response.status_code == 200

        data = response.json()

        assert data["overall_score"] == 0.85
        assert data["metrics"]["f1"] == 0.85
        assert data["not_applicable_cases"] == 0

        performance = data["performance"]

        assert performance["total_results"] == 5
        assert performance["completed_cases"] == 5
        assert performance["failed_cases"] == 0
        assert performance["not_applicable_cases"] == 0

        calculate_mock.assert_not_awaited()
        redis.get.assert_awaited_once()
        redis.set.assert_not_awaited()

    finally:
        app.dependency_overrides.pop(get_redis, None)


def test_get_evaluation_run_summary_cache_miss():
    run_id = uuid4()

    summary = {
        "model": None,
        "overall_score": 0.75,
        "metrics": {
            "f1": 0.75,
        },
        "feedback": {
            "overall": ("Moderate overall evaluation performance with some areas for improvement."),
            "strengths": [
                "The evaluation produced measurable completed-case results.",
                ("Responses demonstrate moderate alignment with expected answers."),
                ("The evaluation pipeline completed successfully for the available cases."),
            ],
            "weaknesses": [
                "F1 performance leaves room for improvement.",
                ("Some responses may differ materially from expected answers."),
                "Additional consistency is needed across evaluated cases.",
            ],
            "patterns": [
                ("Moderate answer alignment is visible across the evaluated results."),
                ("Some variation exists between generated responses and expected answers."),
                ("The current results indicate opportunities to improve consistency."),
            ],
            "recommendations": [
                "Improve alignment with expected answers.",
                "Increase consistency across generated responses.",
                "Continue monitoring F1 performance across future runs.",
            ],
            "evaluator_feedback": [],
        },
        "total_results": 2,
        "completed_cases": 2,
        "failed_cases": 0,
        "not_applicable_cases": 0,
        "performance": {
            "total_results": 2,
            "completed_cases": 2,
            "failed_cases": 0,
            "not_applicable_cases": 0,
            "duration_ms": 10000,
            "total_model_latency_ms": 6000,
            "avg_model_latency_ms": 3000.0,
            "min_model_latency_ms": 2000,
            "p50_model_latency_ms": 3000.0,
            "p95_model_latency_ms": 4000.0,
            "p99_model_latency_ms": 4000.0,
            "max_model_latency_ms": 4000,
            "input_tokens": 250,
            "output_tokens": 450,
            "total_tokens": 700,
            "throughput_cases_per_second": 0.2,
            "cost": {
                "input_cost": 0.001,
                "output_cost": 0.002,
                "total_cost": 0.003,
                "currency": "USD",
            },
        },
    }

    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()

    app.dependency_overrides[get_redis] = lambda: redis

    try:
        with (
            patch(
                "app.api.v1.evaluation.evaluation.EvaluationSummaryPersistenceService.get",
                new=AsyncMock(return_value=None),
            ) as persistence_get_mock,
            patch(
                "app.api.v1.evaluation.evaluation.EvaluationRunSummaryService.calculate",
                new=AsyncMock(return_value=summary),
            ) as calculate_mock,
        ):
            response = client.get(f"/api/v1/evaluation-runs/{run_id}/summary")

        assert response.status_code == 200

        data = response.json()

        assert data["overall_score"] == 0.75
        assert data["metrics"]["f1"] == 0.75
        assert data["not_applicable_cases"] == 0

        performance = data["performance"]

        assert performance["total_results"] == 2
        assert performance["completed_cases"] == 2
        assert performance["failed_cases"] == 0
        assert performance["not_applicable_cases"] == 0

        persistence_get_mock.assert_awaited_once_with(
            ANY,
            run_id,
        )

        calculate_mock.assert_awaited_once_with(
            ANY,
            run_id,
        )

        redis.get.assert_awaited_once()
        redis.set.assert_awaited_once()

    finally:
        app.dependency_overrides.pop(get_redis, None)


def test_get_evaluation_run_summary_works_when_redis_get_fails():
    run_id = uuid4()

    redis = MagicMock()
    redis.get = AsyncMock(side_effect=RuntimeError("Redis unavailable"))
    redis.set = AsyncMock()

    summary = {
        "model": None,
        "overall_score": 0.70,
        "metrics": {
            "f1": 0.70,
        },
        "feedback": {
            "overall": ("Moderate overall evaluation performance with some areas for improvement."),
            "strengths": [
                "The evaluation produced a measurable F1 score.",
                "Completed cases provide useful evaluation evidence.",
                ("The summary remains available despite the Redis cache failure."),
            ],
            "weaknesses": [
                "F1 performance indicates room for improvement.",
                ("Some generated responses may not fully align with expected answers."),
                ("Further consistency would improve overall evaluation quality."),
            ],
            "patterns": [
                "Moderate alignment with expected answers is observed.",
                ("Generated responses show opportunities for better reference alignment."),
                "Evaluation quality can vary across completed cases.",
            ],
            "recommendations": [
                "Improve alignment with expected answers.",
                "Increase consistency of generated responses.",
                ("Continue evaluating F1 performance across subsequent runs."),
            ],
            "evaluator_feedback": [],
        },
        "total_results": 1,
        "completed_cases": 1,
        "failed_cases": 0,
        "not_applicable_cases": 0,
        "performance": {
            "total_results": 1,
            "completed_cases": 1,
            "failed_cases": 0,
            "not_applicable_cases": 0,
            "duration_ms": 1000,
            "total_model_latency_ms": 500,
            "avg_model_latency_ms": 500.0,
            "min_model_latency_ms": 500,
            "p50_model_latency_ms": 500.0,
            "p95_model_latency_ms": 500.0,
            "p99_model_latency_ms": 500.0,
            "max_model_latency_ms": 500,
            "input_tokens": 10,
            "output_tokens": 20,
            "total_tokens": 30,
            "throughput_cases_per_second": 1.0,
            "cost": {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "currency": "USD",
            },
        },
    }

    app.dependency_overrides[get_redis] = lambda: redis

    try:
        with (
            patch(
                "app.api.v1.evaluation.evaluation.EvaluationSummaryPersistenceService.get",
                new=AsyncMock(return_value=None),
            ) as persistence_get_mock,
            patch(
                "app.api.v1.evaluation.evaluation.EvaluationRunSummaryService.calculate",
                new=AsyncMock(return_value=summary),
            ) as calculate_mock,
        ):
            response = client.get(f"/api/v1/evaluation-runs/{run_id}/summary")

        assert response.status_code == 200
        assert response.json()["overall_score"] == 0.70
        assert response.json()["not_applicable_cases"] == 0

        performance = response.json()["performance"]

        assert performance["total_results"] == 1
        assert performance["completed_cases"] == 1
        assert performance["failed_cases"] == 0
        assert performance["not_applicable_cases"] == 0

        persistence_get_mock.assert_awaited_once_with(
            ANY,
            run_id,
        )

        calculate_mock.assert_awaited_once_with(
            ANY,
            run_id,
        )

    finally:
        app.dependency_overrides.pop(get_redis, None)
