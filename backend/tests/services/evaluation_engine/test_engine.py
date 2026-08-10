import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.models.evaluation import EvaluationRunStatus
from app.services.evaluation_engine.engine import EvaluationEngine
from app.services.evaluators.base import EvaluationScore


class FakeEvaluator:
    def __init__(self, name: str, score: float):
        self._name = name
        self._score = score

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(
        self,
        *,
        expected_output,
        actual_output,
        context=None,
    ):
        return EvaluationScore(
            metric=self._name,
            score=self._score,
            feedback=f"{self._name} evaluated.",
        )


class FakeRegistry:
    def __init__(self):
        self.evaluators = {
            "exact_match": FakeEvaluator("exact_match", 1.0),
            "f1": FakeEvaluator("f1", 0.5),
        }

    def get(self, name):
        evaluator = self.evaluators.get(name)

        if evaluator is None:
            raise ValueError(f"Unknown evaluator: {name}")

        return evaluator


@pytest.mark.asyncio
async def test_engine_executes_evaluation():
    run_id = uuid4()
    model_id = uuid4()
    dataset_version_id = uuid4()
    case_id = uuid4()

    run = SimpleNamespace(
        id=run_id,
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        configuration={
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

    case = SimpleNamespace(
        id=case_id,
        input="What is RAG?",
        expected_output="RAG combines retrieval and generation.",
    )

    model = SimpleNamespace(
        id=model_id,
        model_identifier="mock-model",
        configuration={},
        is_active=True,
    )

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalar_one_or_none=lambda: model
        )
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock(
        return_value=SimpleNamespace(
            output="RAG combines retrieval and generation.",
            trace=None,
            latency_ms=10,
            input_tokens=5,
            output_tokens=5,
            total_tokens=10,
        )
    )

    evaluator_registry = FakeRegistry()

    scoring_service = MagicMock()

    scoring_service.calculate.return_value = SimpleNamespace(
        score=0.75,
        metadata={
            "strategy": "weighted",
            "weights": {
                "exact_match": 0.5,
                "f1": 0.5,
            },
        },
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    # Patch service-level database operations used by the engine.
    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(
        return_value=run
    )

    engine_module.DatasetCaseService.list = AsyncMock(
        return_value=[case]
    )

    engine_module.EvaluationResultService.create = AsyncMock()

    result = await engine.execute(run_id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 1
    assert result.completed_cases == 1
    assert result.failed_cases == 0

    model_gateway.generate.assert_awaited_once()

    scoring_service.calculate.assert_called_once()

    engine_module.EvaluationResultService.create.assert_awaited_once()

    saved_result = (
        engine_module.EvaluationResultService.create.call_args.kwargs
    )

    assert saved_result["status"] == "completed"
    assert saved_result["actual_output"] == (
        "RAG combines retrieval and generation."
    )

    assert saved_result["scores"]["exact_match"]["score"] == 1.0
    assert saved_result["scores"]["f1"]["score"] == 0.5
    assert saved_result["scores"]["overall"]["score"] == 0.75