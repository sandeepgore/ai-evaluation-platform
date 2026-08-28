from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_type import EvaluationType
from app.services.evaluation_engine.engine import EvaluationEngine
from app.services.evaluators.base import (
    EvaluationScore,
    EvaluatorMetadata,
)
from app.services.evaluators.registry import create_default_registry


class FakeEvaluator:
    def __init__(
        self,
        name: str,
        score: float,
    ):
        self._name = name
        self._score = score

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> EvaluatorMetadata:
        return EvaluatorMetadata(
            category="general",
            description=f"Fake evaluator for {self._name}.",
            required_inputs=[
                "expected_output",
                "actual_output",
            ],
            requires_reference=True,
            requires_context=False,
            requires_llm=False,
            applicable_to=["text"],
            tags=[],
        )

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


class FakeLLMJudgeEvaluator(FakeEvaluator):
    @property
    def metadata(self) -> EvaluatorMetadata:
        return EvaluatorMetadata(
            category="general",
            description="Fake LLM judge evaluator.",
            required_inputs=[
                "expected_output",
                "actual_output",
            ],
            requires_reference=True,
            requires_context=False,
            requires_llm=True,
            applicable_to=["text"],
            tags=[],
        )


class FakeRegistry:
    def __init__(self):
        self.evaluators = {
            "exact_match": FakeEvaluator(
                "exact_match",
                1.0,
            ),
            "f1": FakeEvaluator(
                "f1",
                0.5,
            ),
            "llm_judge": FakeLLMJudgeEvaluator(
                "llm_judge",
                0.9,
            ),
        }

    def get(self, name):
        evaluator = self.evaluators.get(name)

        if evaluator is None:
            raise ValueError(f"Unknown evaluator: {name}")

        return evaluator

    def register(self, evaluator):
        self.evaluators[evaluator.name] = evaluator


def create_model():
    return SimpleNamespace(
        id=uuid4(),
        name="Mock Model",
        provider="mock",
        model_identifier="mock-model",
        configuration={},
        is_active=True,
    )


def create_case(
    input_text: str,
    expected_output: str,
):
    return SimpleNamespace(
        id=uuid4(),
        input=input_text,
        expected_output=expected_output,
    )


def create_run(
    *,
    model_id,
    dataset_version_id,
    evaluation_type=EvaluationType.TEXT,
    execution_mode="sequential",
    batch_size=10,
):
    return SimpleNamespace(
        id=uuid4(),
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        evaluation_type=evaluation_type,
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

    result = MagicMock()
    result.scalar_one_or_none.return_value = model
    result.scalars.return_value.all.return_value = []

    db.execute = AsyncMock(
        return_value=result,
    )

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

    return (
        db,
        evaluator_registry,
        scoring_service,
    )


def mock_run_summary_services(
    monkeypatch,
    engine_module,
    *,
    overall_score=0.75,
):
    monkeypatch.setattr(
        engine_module.EvaluationRunSummaryService,
        "calculate",
        AsyncMock(
            return_value={
                "model": None,
                "overall_score": overall_score,
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
async def test_engine_executes_evaluation_sequential(monkeypatch):
    model = create_model()

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
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
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

    mock_run_summary_services(
        monkeypatch,
        engine_module,
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(
            return_value=[
                case_1,
                case_2,
            ]
        ),
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 2
    assert result.completed_cases == 2
    assert result.failed_cases == 0

    assert model_gateway.generate.await_count == 2

    expected_configuration = {
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
    }

    model_gateway.generate.assert_any_await(
        prompt="What is RAG?",
        configuration=expected_configuration,
    )

    model_gateway.generate.assert_any_await(
        prompt="What is an LLM?",
        configuration=expected_configuration,
    )

    model_gateway.generate_batch.assert_not_awaited()

    assert engine_module.EvaluationResultService.create.await_count == 2

    assert scoring_service.calculate.call_count == 2


@pytest.mark.asyncio
async def test_engine_executes_evaluation_batch(monkeypatch):
    model = create_model()

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
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
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

    mock_run_summary_services(
        monkeypatch,
        engine_module,
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(
            return_value=[
                case_1,
                case_2,
            ]
        ),
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

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
async def test_engine_batch_respects_batch_size(monkeypatch):
    model = create_model()

    cases = [
        create_case(
            "question 1",
            "answer 1",
        ),
        create_case(
            "question 2",
            "answer 2",
        ),
        create_case(
            "question 3",
            "answer 3",
        ),
    ]

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
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

    mock_run_summary_services(
        monkeypatch,
        engine_module,
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

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

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
async def test_engine_persists_scores_and_feedback(monkeypatch):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
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

    mock_run_summary_services(
        monkeypatch,
        engine_module,
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    evaluation_result_create = AsyncMock(
        return_value=SimpleNamespace(
            id=uuid4(),
            feedback=None,
        )
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    await engine.execute(run.id)

    evaluation_result_create.assert_awaited_once()

    saved_result = evaluation_result_create.call_args.kwargs

    assert saved_result["status"] == "completed"

    assert saved_result["actual_output"] == ("RAG combines retrieval and generation.")

    assert saved_result["expected_output"] == ("RAG combines retrieval and generation.")

    assert saved_result["scores"]["exact_match"]["score"] == 1.0
    assert saved_result["scores"]["f1"]["score"] == 0.5
    assert saved_result["scores"]["overall"]["score"] == 0.75

    assert "exact_match: exact_match evaluated." in saved_result["feedback"]

    assert "f1: f1 evaluated." in saved_result["feedback"]


@pytest.mark.asyncio
async def test_engine_rejects_reference_evaluator_without_reference_before_model_execution(
    monkeypatch,
):
    model = create_model()

    case = SimpleNamespace(
        id=uuid4(),
        input="What is RAG?",
        expected_output=None,
        case_metadata=None,
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        execution_mode="sequential",
    )

    run.configuration["evaluators"] = [
        {
            "name": "exact_match",
            "weight": 1.0,
        }
    ]

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalar_one_or_none=lambda: model,
        )
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()
    model_gateway.generate_batch = AsyncMock()

    scoring_service = MagicMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=create_default_registry(),
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    evaluation_result_create = AsyncMock()

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    with pytest.raises(HTTPException) as exc_info:
        await engine.execute(run.id)

    assert exc_info.value.status_code == 400
    assert "reference" in str(exc_info.value.detail).lower()

    assert run.status == EvaluationRunStatus.PENDING

    model_gateway.generate.assert_not_awaited()
    model_gateway.generate_batch.assert_not_awaited()

    evaluation_result_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_engine_rejects_context_evaluator_without_context_before_model_execution(
    monkeypatch,
):
    model = create_model()

    case = SimpleNamespace(
        id=uuid4(),
        input="What is RAG?",
        expected_output="RAG combines retrieval and generation.",
        case_metadata=None,
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        execution_mode="sequential",
        evaluation_type=EvaluationType.RAG,
    )

    run.configuration["evaluators"] = [
        {
            "name": "faithfulness",
            "weight": 1.0,
        }
    ]

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalar_one_or_none=lambda: model,
        )
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()
    model_gateway.generate_batch = AsyncMock()

    scoring_service = MagicMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=create_default_registry(),
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    evaluation_result_create = AsyncMock()

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    with pytest.raises(HTTPException) as exc_info:
        await engine.execute(run.id)

    assert exc_info.value.status_code == 400
    assert "context" in str(exc_info.value.detail).lower()

    assert run.status == EvaluationRunStatus.PENDING

    model_gateway.generate.assert_not_awaited()
    model_gateway.generate_batch.assert_not_awaited()

    evaluation_result_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_engine_rejects_llm_evaluator_without_llm_before_model_execution(
    monkeypatch,
):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    run.configuration["evaluators"] = [
        {
            "name": "llm_judge",
            "weight": 1.0,
        }
    ]

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalar_one_or_none=lambda: model,
        )
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()
    model_gateway.generate_batch = AsyncMock()

    scoring_service = MagicMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=create_default_registry(),
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    evaluation_result_create = AsyncMock()

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    with pytest.raises(HTTPException) as exc_info:
        await engine.execute(run.id)

    assert exc_info.value.status_code == 400
    assert "llm" in str(exc_info.value.detail).lower()

    assert run.status == EvaluationRunStatus.PENDING

    model_gateway.generate.assert_not_awaited()
    model_gateway.generate_batch.assert_not_awaited()

    evaluation_result_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_engine_accepts_llm_evaluator_when_llm_is_available(
    monkeypatch,
):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    run.configuration["evaluators"] = [
        {
            "name": "llm_judge",
            "weight": 1.0,
        }
    ]

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock(
        return_value=create_response("RAG combines retrieval and generation.")
    )

    model_gateway.generate_batch = AsyncMock()

    judge_model_gateway = MagicMock()

    judge_model_gateway.generate = AsyncMock(
        return_value=create_response(
            '{"score": 0.95, "feedback": "The response is correct and relevant."}'
        )
    )

    judge_model_gateway.generate_batch = AsyncMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    mock_run_summary_services(
        monkeypatch,
        engine_module,
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    evaluation_result_create = AsyncMock(
        return_value=SimpleNamespace(
            id=uuid4(),
            feedback=None,
        )
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    monkeypatch.setattr(
        engine,
        "_resolve_judge_model_gateway",
        AsyncMock(
            return_value=(
                judge_model_gateway,
                {},
                create_model(),
            )
        ),
    )

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 1
    assert result.completed_cases == 1
    assert result.failed_cases == 0

    model_gateway.generate.assert_awaited_once()
    assert judge_model_gateway.generate.await_count == 2

    evaluation_result_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_engine_rejects_invalid_llm_available_configuration(
    monkeypatch,
):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    run.configuration["llm_available"] = "true"

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalar_one_or_none=lambda: model,
        )
    )

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()
    model_gateway.generate_batch = AsyncMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=create_default_registry(),
        scoring_service=MagicMock(),
    )

    from app.services.evaluation_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    evaluation_result_create = AsyncMock()

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        evaluation_result_create,
    )

    with pytest.raises(HTTPException) as exc_info:
        await engine.execute(run.id)

    assert exc_info.value.status_code == 400
    assert "llm_available" in str(exc_info.value.detail)

    assert run.status == EvaluationRunStatus.PENDING

    model_gateway.generate.assert_not_awaited()
    model_gateway.generate_batch.assert_not_awaited()

    evaluation_result_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_evaluate_case_sends_persisted_feedback_to_aggregation_service():
    model = create_model()

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    response = create_response("RAG combines retrieval and generation.")

    evaluator = MagicMock()
    evaluator.name = "exact_match"
    evaluator.evaluate = AsyncMock(
        return_value=SimpleNamespace(
            metric="exact_match",
            score=1.0,
            feedback="Response matches the reference.",
            metadata={},
        )
    )

    aggregation_service = AsyncMock()

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=MagicMock(),
        feedback_aggregation_service=aggregation_service,
    )

    engine.scoring_service.calculate.return_value = SimpleNamespace(
        score=1.0,
        metadata={},
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback="exact_match: Response matches the reference.",
    )

    from app.services.evaluation_engine import engine as engine_module

    from unittest.mock import patch

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(
            return_value=persisted_result,
        ),
    ):
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (evaluator, 1.0),
            ],
            scoring_configuration={},
        )

    aggregation_service.accept.assert_awaited_once_with(
        run.id,
        persisted_result.id,
        persisted_result.feedback,
    )

    assert run.completed_cases == 1


@pytest.mark.asyncio
async def test_evaluate_case_does_not_send_empty_feedback_to_aggregation_service():
    model = create_model()

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    response = create_response("RAG combines retrieval and generation.")

    evaluator = MagicMock()
    evaluator.name = "exact_match"
    evaluator.evaluate = AsyncMock(
        return_value=SimpleNamespace(
            metric="exact_match",
            score=1.0,
            feedback=None,
            metadata={},
        )
    )

    aggregation_service = AsyncMock()

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=MagicMock(),
        feedback_aggregation_service=aggregation_service,
    )

    engine.scoring_service.calculate.return_value = SimpleNamespace(
        score=1.0,
        metadata={},
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback=None,
    )

    from app.services.evaluation_engine import engine as engine_module

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(
            return_value=persisted_result,
        ),
    ):
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (evaluator, 1.0),
            ],
            scoring_configuration={},
        )

    aggregation_service.accept.assert_not_awaited()

    assert run.completed_cases == 1


@pytest.mark.asyncio
async def test_evaluate_case_succeeds_without_aggregation_service():
    model = create_model()

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    response = create_response("RAG combines retrieval and generation.")

    evaluator = MagicMock()
    evaluator.name = "exact_match"
    evaluator.evaluate = AsyncMock(
        return_value=SimpleNamespace(
            metric="exact_match",
            score=1.0,
            feedback="Response matches the reference.",
            metadata={},
        )
    )

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=MagicMock(),
        feedback_aggregation_service=None,
    )

    engine.scoring_service.calculate.return_value = SimpleNamespace(
        score=1.0,
        metadata={},
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback="exact_match: Response matches the reference.",
    )

    from app.services.evaluation_engine import engine as engine_module

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(
            return_value=persisted_result,
        ),
    ):
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (evaluator, 1.0),
            ],
            scoring_configuration={},
        )

    assert run.completed_cases == 1


@pytest.mark.asyncio
async def test_evaluate_case_aggregation_failure_does_not_fail_case():
    model = create_model()

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    response = create_response("RAG combines retrieval and generation.")

    evaluator = MagicMock()
    evaluator.name = "exact_match"
    evaluator.evaluate = AsyncMock(
        return_value=SimpleNamespace(
            metric="exact_match",
            score=1.0,
            feedback="Response matches the reference.",
            metadata={},
        )
    )

    aggregation_service = AsyncMock()

    aggregation_service.accept.side_effect = RuntimeError("Reducer temporarily unavailable")

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=MagicMock(),
        feedback_aggregation_service=aggregation_service,
    )

    engine.scoring_service.calculate.return_value = SimpleNamespace(
        score=1.0,
        metadata={},
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback="exact_match: Response matches the reference.",
    )

    from app.services.evaluation_engine import engine as engine_module

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(
            return_value=persisted_result,
        ),
    ):
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (evaluator, 1.0),
            ],
            scoring_configuration={},
        )

    assert run.completed_cases == 1

    aggregation_service.accept.assert_awaited_once_with(
        run.id,
        persisted_result.id,
        persisted_result.feedback,
    )


@pytest.mark.asyncio
async def test_engine_finalizes_rolling_feedback_and_persists_summary(
    monkeypatch,
):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock(
        return_value=create_response("RAG combines retrieval and generation.")
    )

    model_gateway.generate_batch = AsyncMock()

    aggregation_service = AsyncMock()

    final_feedback = {
        "overall": "Strong overall performance.",
        "strengths": [
            "High relevance",
            "Strong correctness",
        ],
        "weaknesses": [
            "Some answers lack detail",
        ],
        "patterns": [
            "Responses are generally concise.",
        ],
        "recommendations": [
            "Add supporting detail where needed.",
        ],
        "evaluator_feedback": [],
    }

    aggregation_service.finalize = AsyncMock(
        return_value={
            "finalized": True,
            "feedback": final_feedback,
            "source_count": 1,
            "revision": 1,
        }
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
        feedback_aggregation_service=aggregation_service,
    )

    from app.services.evaluation_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback="exact_match: response is correct.",
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(return_value=persisted_result),
    )

    deterministic_summary = {
        "model": {
            "id": model.id,
            "name": "Mock Model",
            "provider": "mock",
            "model_identifier": "mock-model",
        },
        "overall_score": 0.75,
        "metrics": {
            "exact_match": 0.75,
            "f1": 0.75,
        },
        "total_results": 1,
        "completed_cases": 1,
        "failed_cases": 0,
        "feedback": {
            "overall": "Deterministic feedback.",
            "strengths": [
                "Test strength one.",
                "Test strength two.",
                "Test strength three.",
            ],
            "weaknesses": [
                "Test weakness one.",
                "Test weakness two.",
                "Test weakness three.",
            ],
            "patterns": [
                "Test pattern one.",
                "Test pattern two.",
                "Test pattern three.",
            ],
            "recommendations": [
                "Test recommendation one.",
                "Test recommendation two.",
                "Test recommendation three.",
            ],
            "evaluator_feedback": [],
        },
        "performance": {
            "duration_ms": 10,
            "total_model_latency_ms": 10,
            "avg_model_latency_ms": 10.0,
            "min_model_latency_ms": 10,
            "p50_model_latency_ms": 10.0,
            "p95_model_latency_ms": 10.0,
            "p99_model_latency_ms": 10.0,
            "max_model_latency_ms": 10,
            "input_tokens": 5,
            "output_tokens": 5,
            "total_tokens": 10,
            "throughput_cases_per_second": 100.0,
            "cost": {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "currency": "USD",
            },
        },
    }

    summary_calculate = AsyncMock(
        return_value=deterministic_summary,
    )

    summary_save = AsyncMock(
        return_value=SimpleNamespace(
            evaluation_run_id=run.id,
        )
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunSummaryService,
        "calculate",
        summary_calculate,
    )

    monkeypatch.setattr(
        engine_module.EvaluationSummaryPersistenceService,
        "save",
        summary_save,
    )

    result = await engine.execute(run.id)

    aggregation_service.finalize.assert_awaited_once_with(
        run.id,
    )

    summary_calculate.assert_awaited_once_with(
        db,
        run.id,
    )

    summary_save.assert_awaited_once()

    persisted_summary = summary_save.await_args

    assert persisted_summary.args[0] is db
    assert persisted_summary.args[1] == run.id

    summary_payload = persisted_summary.args[2]

    assert summary_payload["overall_score"] == 0.75
    assert summary_payload["metrics"] == {
        "exact_match": 0.75,
        "f1": 0.75,
    }

    feedback = summary_payload["feedback"]
    assert len(feedback["strengths"]) >= 3
    assert len(feedback["weaknesses"]) >= 3
    assert len(feedback["patterns"]) >= 3
    assert len(feedback["recommendations"]) >= 3

    assert result.status == EvaluationRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_engine_persists_deterministic_feedback_without_rolling_reducer(
    monkeypatch,
):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()

    model_gateway.generate = AsyncMock(
        return_value=create_response("RAG combines retrieval and generation.")
    )

    model_gateway.generate_batch = AsyncMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
        feedback_aggregation_service=None,
    )

    from app.services.evaluation_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[case]),
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(
            return_value=SimpleNamespace(
                id=uuid4(),
                feedback=None,
            )
        ),
    )
    deterministic_feedback = {
        "overall": "Moderate overall performance.",
        "strengths": [
            "Test strength one.",
            "Test strength two.",
            "Test strength three.",
        ],
        "weaknesses": [
            "F1 can be improved.",
            "Some responses need better alignment.",
            "Additional consistency is needed.",
        ],
        "patterns": [
            "Responses show moderate alignment.",
            "Some variation exists across cases.",
            "Metric performance indicates room for improvement.",
        ],
        "recommendations": [
            "Improve answer alignment.",
            "Increase response consistency.",
            "Continue monitoring evaluation performance.",
        ],
        "evaluator_feedback": [],
    }
    deterministic_summary = {
        "overall_score": 0.75,
        "metrics": {
            "exact_match": 0.75,
            "f1": 0.75,
        },
        "feedback": deterministic_feedback,
        "model": None,
        "total_results": 1,
        "completed_cases": 1,
        "failed_cases": 0,
        "performance": {},
    }

    summary_calculate = AsyncMock(
        return_value=deterministic_summary,
    )

    summary_save = AsyncMock(
        return_value=SimpleNamespace(
            evaluation_run_id=run.id,
        )
    )

    monkeypatch.setattr(
        engine_module.EvaluationRunSummaryService,
        "calculate",
        summary_calculate,
    )

    monkeypatch.setattr(
        engine_module.EvaluationSummaryPersistenceService,
        "save",
        summary_save,
    )

    result = await engine.execute(run.id)

    assert engine.feedback_aggregation_service is None

    summary_calculate.assert_awaited_once_with(
        db,
        run.id,
    )

    summary_save.assert_awaited_once()

    summary_payload = summary_save.await_args.args[2]

    feedback = summary_payload["feedback"]
    assert len(feedback["strengths"]) >= 3
    assert len(feedback["weaknesses"]) >= 3
    assert len(feedback["patterns"]) >= 3
    assert len(feedback["recommendations"]) >= 3

    assert result.status == EvaluationRunStatus.COMPLETED
