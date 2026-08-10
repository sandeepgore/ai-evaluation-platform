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


def create_model():
    return SimpleNamespace(
        id=uuid4(),
        model_identifier="mock-model",
        configuration={},
        is_active=True,
    )


def create_case(input_text: str, expected_output: str):
    return SimpleNamespace(
        id=uuid4(),
        input=input_text,
        expected_output=expected_output,
    )


def create_run(
    *,
    model_id,
    dataset_version_id,
    execution_mode="sequential",
    batch_size=10,
):
    return SimpleNamespace(
        id=uuid4(),
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        configuration={
            "execution_mode": execution_mode,
            "batch_size": batch_size,
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


def create_response(output: str):
    return SimpleNamespace(
        output=output,
        trace=None,
        latency_ms=10,
        input_tokens=5,
        output_tokens=5,
        total_tokens=10,
    )


def create_engine_mocks(model):
    db = MagicMock()

    db.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: model))

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

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

    return db, evaluator_registry, scoring_service


@pytest.mark.asyncio
async def test_engine_executes_evaluation_sequential():
    """
    Sequential mode executes one model request per case.
    """

    model = create_model()

    dataset_version_id = uuid4()

    case_1 = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    case_2 = create_case(
        "What is an LLM?",
        "An LLM is a large language model.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=dataset_version_id,
        execution_mode="sequential",
    )

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock(
        side_effect=[
            create_response("RAG combines retrieval and generation."),
            create_response("An LLM is a large language model."),
        ]
    )

    model_gateway.generate_batch = AsyncMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(return_value=run)

    engine_module.DatasetCaseService.list = AsyncMock(return_value=[case_1, case_2])

    engine_module.EvaluationResultService.create = AsyncMock()

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 2
    assert result.completed_cases == 2
    assert result.failed_cases == 0

    assert model_gateway.generate.await_count == 2

    model_gateway.generate.assert_any_await(
        prompt="What is RAG?",
        configuration={
            "execution_mode": "sequential",
            "batch_size": 10,
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

    model_gateway.generate.assert_any_await(
        prompt="What is an LLM?",
        configuration={
            "execution_mode": "sequential",
            "batch_size": 10,
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

    model_gateway.generate_batch.assert_not_awaited()

    assert engine_module.EvaluationResultService.create.await_count == 2

    assert scoring_service.calculate.call_count == 2


@pytest.mark.asyncio
async def test_engine_executes_evaluation_batch():
    """
    Batch mode executes cases using generate_batch().
    """

    model = create_model()

    dataset_version_id = uuid4()

    case_1 = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    case_2 = create_case(
        "What is an LLM?",
        "An LLM is a large language model.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=dataset_version_id,
        execution_mode="batch",
        batch_size=10,
    )

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock()

    model_gateway.generate_batch = AsyncMock(
        return_value=[
            create_response("RAG combines retrieval and generation."),
            create_response("An LLM is a large language model."),
        ]
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(return_value=run)

    engine_module.DatasetCaseService.list = AsyncMock(return_value=[case_1, case_2])

    engine_module.EvaluationResultService.create = AsyncMock()

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 2
    assert result.completed_cases == 2
    assert result.failed_cases == 0

    model_gateway.generate_batch.assert_awaited_once_with(
        prompts=[
            "What is RAG?",
            "What is an LLM?",
        ],
        configuration={
            "execution_mode": "batch",
            "batch_size": 10,
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

    model_gateway.generate.assert_not_awaited()

    assert engine_module.EvaluationResultService.create.await_count == 2

    assert scoring_service.calculate.call_count == 2


@pytest.mark.asyncio
async def test_engine_batch_respects_batch_size():
    """
    Batch mode should split cases according to batch_size.
    """

    model = create_model()

    dataset_version_id = uuid4()

    cases = [
        create_case("question 1", "answer 1"),
        create_case("question 2", "answer 2"),
        create_case("question 3", "answer 3"),
    ]

    run = create_run(
        model_id=model.id,
        dataset_version_id=dataset_version_id,
        execution_mode="batch",
        batch_size=2,
    )

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock()

    model_gateway.generate_batch = AsyncMock(
        side_effect=[
            [
                create_response("answer 1"),
                create_response("answer 2"),
            ],
            [
                create_response("answer 3"),
            ],
        ]
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(return_value=run)

    engine_module.DatasetCaseService.list = AsyncMock(return_value=cases)

    engine_module.EvaluationResultService.create = AsyncMock()

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 3
    assert result.completed_cases == 3
    assert result.failed_cases == 0

    assert model_gateway.generate_batch.await_count == 2

    calls = model_gateway.generate_batch.await_args_list

    assert calls[0].kwargs["prompts"] == [
        "question 1",
        "question 2",
    ]

    assert calls[1].kwargs["prompts"] == [
        "question 3",
    ]

    model_gateway.generate.assert_not_awaited()

    assert engine_module.EvaluationResultService.create.await_count == 3


@pytest.mark.asyncio
async def test_engine_persists_scores_and_feedback():
    """
    Verify that evaluator scores, overall score and feedback
    are persisted correctly.
    """

    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        execution_mode="sequential",
    )

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock(
        return_value=create_response("RAG combines retrieval and generation.")
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(return_value=run)

    engine_module.DatasetCaseService.list = AsyncMock(return_value=[case])

    engine_module.EvaluationResultService.create = AsyncMock()

    await engine.execute(run.id)

    engine_module.EvaluationResultService.create.assert_awaited_once()

    saved_result = engine_module.EvaluationResultService.create.call_args.kwargs

    assert saved_result["status"] == "completed"

    assert saved_result["actual_output"] == ("RAG combines retrieval and generation.")

    assert saved_result["expected_output"] == ("RAG combines retrieval and generation.")

    assert saved_result["scores"]["exact_match"]["score"] == 1.0
    assert saved_result["scores"]["f1"]["score"] == 0.5
    assert saved_result["scores"]["overall"]["score"] == 0.75

    assert "exact_match: exact_match evaluated." in (saved_result["feedback"])

    assert "f1: f1 evaluated." in saved_result["feedback"]
