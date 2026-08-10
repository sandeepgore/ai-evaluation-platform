import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

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
async def test_engine_executes_evaluation_in_batches():
    """
    Batch mode executes model inference through generate_batch()
    and processes responses in the same order as the dataset cases.
    """

    run_id = uuid4()
    model_id = uuid4()
    dataset_version_id = uuid4()

    cases = [
        SimpleNamespace(
            id=uuid4(),
            input="Question 1",
            expected_output="Answer 1",
        ),
        SimpleNamespace(
            id=uuid4(),
            input="Question 2",
            expected_output="Answer 2",
        ),
        SimpleNamespace(
            id=uuid4(),
            input="Question 3",
            expected_output="Answer 3",
        ),
    ]

    run = SimpleNamespace(
        id=run_id,
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        configuration={
            "execution_mode": "batch",
            "batch_size": 2,
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
        model_identifier="mock-model",
        configuration={},
        is_active=True,
    )

    db = MagicMock()

    db.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: model))

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock()

    model_gateway.generate_batch = AsyncMock(
        side_effect=[
            [
                SimpleNamespace(
                    output="Answer 1",
                    trace=None,
                    latency_ms=10,
                    input_tokens=2,
                    output_tokens=2,
                    total_tokens=4,
                ),
                SimpleNamespace(
                    output="Answer 2",
                    trace=None,
                    latency_ms=10,
                    input_tokens=2,
                    output_tokens=2,
                    total_tokens=4,
                ),
            ],
            [
                SimpleNamespace(
                    output="Answer 3",
                    trace=None,
                    latency_ms=10,
                    input_tokens=2,
                    output_tokens=2,
                    total_tokens=4,
                ),
            ],
        ]
    )

    scoring_service = MagicMock()

    scoring_service.calculate.return_value = SimpleNamespace(
        score=0.75,
        metadata={
            "strategy": "weighted",
        },
    )

    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(return_value=run)

    engine_module.DatasetCaseService.list = AsyncMock(return_value=cases)

    engine_module.EvaluationResultService.create = AsyncMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=FakeRegistry(),
        scoring_service=scoring_service,
    )

    result = await engine.execute(run_id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 3
    assert result.completed_cases == 3
    assert result.failed_cases == 0

    # Three cases with batch_size=2 must produce two
    # generate_batch() calls:
    #
    # Batch 1 -> Question 1, Question 2
    # Batch 2 -> Question 3

    assert model_gateway.generate_batch.await_count == 2

    model_gateway.generate_batch.assert_any_await(
        prompts=[
            "Question 1",
            "Question 2",
        ],
        configuration={
            "execution_mode": "batch",
            "batch_size": 2,
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
            "model": "mock-model",
        },
    )

    model_gateway.generate_batch.assert_any_await(
        prompts=[
            "Question 3",
        ],
        configuration={
            "execution_mode": "batch",
            "batch_size": 2,
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
            "model": "mock-model",
        },
    )

    # Batch mode must not use sequential model generation.
    model_gateway.generate.assert_not_awaited()

    # Three cases should produce three persisted results.
    assert engine_module.EvaluationResultService.create.await_count == 3

    # Scoring must happen once per case.
    assert scoring_service.calculate.call_count == 3
