from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_type import EvaluationType
from app.services.evaluation.dataset_capability import DatasetCapabilities
from app.services.evaluation_engine import engine as engine_module
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


class FakeContextEvaluator:
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
            category="rag",
            description=f"Fake context evaluator for {self._name}.",
            required_inputs=[
                "actual_output",
                "context",
            ],
            requires_reference=False,
            requires_context=True,
            requires_llm=False,
            applicable_to=["rag"],
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
    expected_output: str | None,
    *,
    has_reference: bool = True,
    has_context: bool = False,
    context=None,
):
    return SimpleNamespace(
        id=uuid4(),
        input=input_text,
        expected_output=expected_output,
        context=context,
        case_metadata=None,
        has_reference=has_reference,
        has_context=has_context,
    )


def capabilities_from_cases(cases) -> DatasetCapabilities:
    """Build dataset-level capabilities from the test cases.

    Engine tests use this helper instead of depending on the fake SQLAlchemy
    result returned by the model lookup.
    """
    total_cases = len(cases)

    cases_with_reference = sum(1 for case in cases if case.has_reference)

    cases_with_context = sum(1 for case in cases if case.has_context)

    reference_coverage = cases_with_reference / total_cases if total_cases else 0.0

    context_coverage = cases_with_context / total_cases if total_cases else 0.0

    return DatasetCapabilities(
        total_cases=total_cases,
        cases_with_reference=cases_with_reference,
        cases_without_reference=(total_cases - cases_with_reference),
        cases_with_context=cases_with_context,
        cases_without_context=(total_cases - cases_with_context),
        has_reference=cases_with_reference > 0,
        has_context=cases_with_context > 0,
        all_cases_have_reference=(total_cases > 0 and cases_with_reference == total_cases),
        all_cases_have_context=(total_cases > 0 and cases_with_context == total_cases),
        reference_coverage=reference_coverage,
        context_coverage=context_coverage,
    )


def mock_dataset_capabilities(
    monkeypatch,
    cases,
):
    """Mock dataset-level capability analysis for EvaluationEngine tests.

    DatasetCapabilityService has its own dedicated tests. Engine tests should
    provide the capabilities explicitly so they do not depend on SQLAlchemy
    result-shape details.
    """
    monkeypatch.setattr(
        engine_module.DatasetCapabilityService,
        "analyze_dataset_version",
        AsyncMock(
            return_value=capabilities_from_cases(cases),
        ),
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

    cases = [case_1, case_2]

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

    mock_run_summary_services(
        monkeypatch,
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

    mock_dataset_capabilities(
        monkeypatch,
        cases,
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

    cases = [case_1, case_2]

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

    mock_run_summary_services(
        monkeypatch,
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

    mock_dataset_capabilities(
        monkeypatch,
        cases,
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

    mock_run_summary_services(
        monkeypatch,
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

    mock_dataset_capabilities(
        monkeypatch,
        cases,
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

    mock_run_summary_services(
        monkeypatch,
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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
        has_reference=False,
        has_context=False,
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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
        has_reference=True,
        has_context=False,
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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

    mock_run_summary_services(
        monkeypatch,
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
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

    persisted_summary = summary_save.await_args

    assert persisted_summary.args[0] is db
    assert persisted_summary.args[1] == run.id

    summary_payload = persisted_summary.args[2]

    feedback = summary_payload["feedback"]

    assert len(feedback["strengths"]) >= 3
    assert len(feedback["weaknesses"]) >= 3
    assert len(feedback["patterns"]) >= 3
    assert len(feedback["recommendations"]) >= 3

    assert result.status == EvaluationRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_evaluate_case_marks_reference_metric_not_applicable_when_reference_is_missing():
    run = create_run(
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        None,
        has_reference=False,
        has_context=False,
    )

    response = create_response("RAG combines retrieval and generation.")

    evaluator = MagicMock()
    evaluator.name = "exact_match"

    evaluator.metadata = EvaluatorMetadata(
        category="general",
        description="Reference-based evaluator.",
        required_inputs=[
            "actual_output",
            "expected_output",
        ],
        requires_reference=True,
        requires_context=False,
        requires_llm=False,
        applicable_to=["text"],
        tags=[],
    )

    evaluator.evaluate = AsyncMock()

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=MagicMock(),
    )

    engine.scoring_service.calculate.return_value = SimpleNamespace(
        score=1.0,
        metadata={},
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback=None,
    )

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(return_value=persisted_result),
    ) as evaluation_result_create:
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (evaluator, 1.0),
            ],
            scoring_configuration={},
        )

    saved_result = evaluation_result_create.call_args.kwargs

    exact_match = saved_result["scores"]["exact_match"]

    assert exact_match["status"] == "not_applicable"
    assert exact_match["score"] is None
    assert exact_match["metadata"]["missing_requirements"] == ["reference"]

    evaluator.evaluate.assert_not_awaited()

    assert saved_result["scores"]["overall"]["status"] == "not_applicable"
    assert saved_result["scores"]["overall"]["score"] is None

    engine.scoring_service.calculate.assert_not_called()


@pytest.mark.asyncio
async def test_evaluate_case_marks_context_metric_not_applicable_when_context_is_missing():
    run = create_run(
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.RAG,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        None,
        has_reference=False,
        has_context=False,
    )

    response = create_response("RAG combines retrieval and generation.")

    evaluator = MagicMock()
    evaluator.name = "faithfulness"

    evaluator.metadata = EvaluatorMetadata(
        category="rag",
        description="Context-based evaluator.",
        required_inputs=[
            "actual_output",
            "context",
        ],
        requires_reference=False,
        requires_context=True,
        requires_llm=False,
        applicable_to=["rag"],
        tags=[],
    )

    evaluator.evaluate = AsyncMock()

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=MagicMock(),
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback=None,
    )

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(return_value=persisted_result),
    ) as evaluation_result_create:
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (evaluator, 1.0),
            ],
            scoring_configuration={},
        )

    saved_result = evaluation_result_create.call_args.kwargs

    faithfulness = saved_result["scores"]["faithfulness"]

    assert faithfulness["status"] == "not_applicable"
    assert faithfulness["score"] is None
    assert faithfulness["metadata"]["missing_requirements"] == ["context"]

    evaluator.evaluate.assert_not_awaited()

    assert saved_result["scores"]["overall"]["status"] == "not_applicable"
    assert saved_result["scores"]["overall"]["score"] is None

    engine.scoring_service.calculate.assert_not_called()


@pytest.mark.asyncio
async def test_evaluate_case_scores_only_applicable_metrics():
    run = create_run(
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        None,
        has_reference=False,
        has_context=True,
    )

    response = create_response("RAG combines retrieval and generation.")

    reference_evaluator = MagicMock()
    reference_evaluator.name = "exact_match"

    reference_evaluator.metadata = EvaluatorMetadata(
        category="general",
        description="Reference-based evaluator.",
        required_inputs=[
            "actual_output",
            "expected_output",
        ],
        requires_reference=True,
        requires_context=False,
        requires_llm=False,
        applicable_to=["text"],
        tags=[],
    )

    reference_evaluator.evaluate = AsyncMock()

    context_evaluator = FakeContextEvaluator(
        "faithfulness",
        0.8,
    )

    scoring_service = MagicMock()

    scoring_service.calculate.return_value = SimpleNamespace(
        score=0.8,
        metadata={
            "strategy": "weighted",
            "weights": {
                "faithfulness": 1.0,
            },
        },
    )

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=scoring_service,
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback="faithfulness: faithfulness evaluated.",
    )

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(return_value=persisted_result),
    ) as evaluation_result_create:
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (reference_evaluator, 0.5),
                (context_evaluator, 0.5),
            ],
            scoring_configuration={
                "weights": {
                    "exact_match": 0.5,
                    "faithfulness": 0.5,
                }
            },
        )

    saved_result = evaluation_result_create.call_args.kwargs

    assert saved_result["scores"]["exact_match"]["status"] == ("not_applicable")
    assert saved_result["scores"]["exact_match"]["score"] is None

    assert saved_result["scores"]["faithfulness"]["status"] == ("completed")
    assert saved_result["scores"]["faithfulness"]["score"] == 0.8

    assert saved_result["scores"]["overall"]["status"] == "completed"
    assert saved_result["scores"]["overall"]["score"] == 0.8

    reference_evaluator.evaluate.assert_not_awaited()
    assert scoring_service.calculate.call_count == 1

    scoring_call = scoring_service.calculate.call_args.kwargs

    assert scoring_call["scores"] == {
        "faithfulness": {
            "score": 0.8,
            "status": "completed",
            "metadata": {},
        }
    }


@pytest.mark.asyncio
async def test_evaluate_case_returns_no_overall_score_when_all_metrics_are_not_applicable():
    run = create_run(
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    case = create_case(
        "What is RAG?",
        None,
        has_reference=False,
        has_context=False,
    )

    response = create_response("RAG combines retrieval and generation.")

    exact_match = MagicMock()
    exact_match.name = "exact_match"

    exact_match.metadata = EvaluatorMetadata(
        category="general",
        description="Reference-based evaluator.",
        required_inputs=[
            "actual_output",
            "expected_output",
        ],
        requires_reference=True,
        requires_context=False,
        requires_llm=False,
        applicable_to=["text"],
        tags=[],
    )

    exact_match.evaluate = AsyncMock()

    f1 = MagicMock()
    f1.name = "f1"

    f1.metadata = EvaluatorMetadata(
        category="general",
        description="Reference-based evaluator.",
        required_inputs=[
            "actual_output",
            "expected_output",
        ],
        requires_reference=True,
        requires_context=False,
        requires_llm=False,
        applicable_to=["text"],
        tags=[],
    )

    f1.evaluate = AsyncMock()

    scoring_service = MagicMock()

    engine = EvaluationEngine(
        db=AsyncMock(),
        model_gateway=None,
        evaluator_registry=MagicMock(),
        scoring_service=scoring_service,
    )

    persisted_result = SimpleNamespace(
        id=uuid4(),
        feedback=None,
    )

    with patch.object(
        engine_module.EvaluationResultService,
        "create",
        new=AsyncMock(return_value=persisted_result),
    ) as evaluation_result_create:
        await engine._evaluate_case(
            run=run,
            case=case,
            response=response,
            evaluator_configs=[
                (exact_match, 0.5),
                (f1, 0.5),
            ],
            scoring_configuration={
                "weights": {
                    "exact_match": 0.5,
                    "f1": 0.5,
                }
            },
        )

    saved_result = evaluation_result_create.call_args.kwargs

    assert saved_result["scores"]["exact_match"]["status"] == ("not_applicable")
    assert saved_result["scores"]["exact_match"]["score"] is None

    assert saved_result["scores"]["f1"]["status"] == "not_applicable"
    assert saved_result["scores"]["f1"]["score"] is None

    assert saved_result["scores"]["overall"]["status"] == "not_applicable"
    assert saved_result["scores"]["overall"]["score"] is None

    exact_match.evaluate.assert_not_awaited()
    f1.evaluate.assert_not_awaited()

    scoring_service.calculate.assert_not_called()


@pytest.mark.asyncio
async def test_engine_resolves_simple_prompt_before_model_execution(monkeypatch):
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

    run.configuration["prompt"] = {
        "mode": "simple",
        "instruction": "Answer concisely.",
    }

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
    )

    mock_run_summary_services(monkeypatch)

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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

    await engine.execute(run.id)

    model_gateway.generate.assert_awaited_once()

    call = model_gateway.generate.await_args

    assert call.kwargs["prompt"] == "Answer concisely.\n\nWhat is RAG?"

    # Prompt configuration belongs to the run-level prompt layer,
    # not the provider/model configuration.
    assert "prompt" not in call.kwargs["configuration"]


@pytest.mark.asyncio
async def test_engine_resolves_advanced_prompt_with_case_input_and_context(
    monkeypatch,
):
    model = create_model()

    case = create_case(
        "What is RAG?",
        "RAG combines retrieval and generation.",
        has_context=True,
        context=[
            "RAG retrieves relevant documents.",
            "The generator uses the retrieved context.",
        ],
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.RAG,
        execution_mode="sequential",
    )

    # Use a context evaluator so the case remains eligible.
    run.configuration["evaluators"] = [
        {
            "name": "faithfulness",
            "weight": 1.0,
        }
    ]

    run.configuration["prompt"] = {
        "mode": "advanced",
        "system": "You are a precise AI assistant.",
        "user_template": "Question:\n{{input}}\n\nContext:\n{{context}}",
    }

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    evaluator_registry.register(
        FakeContextEvaluator(
            "faithfulness",
            0.8,
        )
    )

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
    )

    mock_run_summary_services(monkeypatch)

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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

    await engine.execute(run.id)

    model_gateway.generate.assert_awaited_once()

    call = model_gateway.generate.await_args

    assert call.kwargs["prompt"] == (
        "You are a precise AI assistant.\n\n"
        "Question:\nWhat is RAG?\n\n"
        "Context:\n"
        "RAG retrieves relevant documents.\n"
        "The generator uses the retrieved context."
    )


@pytest.mark.asyncio
async def test_engine_without_prompt_preserves_original_case_input(
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

    # Explicitly verify the old behavior remains unchanged.
    assert "prompt" not in run.configuration

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
    )

    mock_run_summary_services(monkeypatch)

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

    mock_dataset_capabilities(
        monkeypatch,
        [case],
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

    await engine.execute(run.id)

    model_gateway.generate.assert_awaited_once_with(
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


@pytest.mark.asyncio
async def test_engine_does_not_call_model_when_no_evaluator_is_applicable(
    monkeypatch,
):
    model = create_model()

    reference_case = create_case(
        "Reference case",
        "Expected answer",
        has_reference=True,
        has_context=False,
    )

    case = create_case(
        "What is RAG?",
        None,
        has_reference=False,
        has_context=False,
    )

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="sequential",
    )

    run.configuration["evaluators"] = [
        {
            "name": "exact_match",
            "weight": 1.0,
        }
    ]

    run.configuration["data_policy"] = {
        "type": "partial",
    }

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()
    model_gateway.generate_batch = AsyncMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    mock_run_summary_services(monkeypatch)

    monkeypatch.setattr(
        engine_module.EvaluationRunService,
        "get_by_id",
        AsyncMock(return_value=run),
    )

    monkeypatch.setattr(
        engine_module.DatasetCaseService,
        "list",
        AsyncMock(return_value=[reference_case, case]),
    )

    mock_dataset_capabilities(
        monkeypatch,
        [reference_case, case],
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

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 2
    assert result.completed_cases == 2
    assert result.failed_cases == 0

    # The reference case is eligible and therefore calls the model.
    # The no-reference case is NOT_APPLICABLE and must not call it.
    model_gateway.generate.assert_awaited_once()
    model_gateway.generate_batch.assert_not_awaited()

    assert evaluation_result_create.await_count == 2

    saved_results = [call.kwargs for call in evaluation_result_create.call_args_list]

    not_applicable_result = next(
        result
        for result in saved_results
        if result["scores"]["exact_match"]["status"] == "not_applicable"
    )

    assert not_applicable_result["status"] == "completed"
    assert not_applicable_result["scores"]["exact_match"]["score"] is None
    assert not_applicable_result["scores"]["overall"]["status"] == "not_applicable"
    assert not_applicable_result["scores"]["overall"]["score"] is None


@pytest.mark.asyncio
async def test_engine_batch_skips_not_applicable_cases_and_preserves_result_mapping(
    monkeypatch,
):
    model = create_model()

    case_1 = create_case(
        "question 1",
        "answer 1",
        has_reference=True,
    )
    case_2 = create_case(
        "question 2",
        None,
        has_reference=False,
    )
    case_3 = create_case(
        "question 3",
        "answer 3",
        has_reference=True,
    )
    case_4 = create_case(
        "question 4",
        None,
        has_reference=False,
    )

    cases = [case_1, case_2, case_3, case_4]

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="batch",
        batch_size=10,
    )

    run.configuration["evaluators"] = [
        {
            "name": "exact_match",
            "weight": 1.0,
        }
    ]

    run.configuration["data_policy"] = {
        "type": "partial",
    }

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()

    model_gateway.generate_batch = AsyncMock(
        return_value=[
            create_response("answer 1"),
            create_response("answer 3"),
        ]
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    mock_run_summary_services(monkeypatch)

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

    mock_dataset_capabilities(
        monkeypatch,
        cases,
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

    result = await engine.execute(run.id)

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.total_cases == 4
    assert result.completed_cases == 4
    assert result.failed_cases == 0

    model_gateway.generate.assert_not_awaited()

    model_gateway.generate_batch.assert_awaited_once_with(
        prompts=[
            "question 1",
            "question 3",
        ],
        configuration={
            "execution_mode": "batch",
            "batch_size": 10,
            "evaluators": [
                {
                    "name": "exact_match",
                    "weight": 1.0,
                }
            ],
            "scoring": {
                "weights": {
                    "exact_match": 0.5,
                    "f1": 0.5,
                }
            },
            "data_policy": {
                "type": "partial",
            },
            "model": "mock-model",
        },
    )

    assert evaluation_result_create.await_count == 4

    saved_results = [call.kwargs for call in evaluation_result_create.call_args_list]

    results_by_case_id = {
        saved_result["dataset_case_id"]: saved_result for saved_result in saved_results
    }

    assert results_by_case_id[case_1.id]["actual_output"] == "answer 1"
    assert results_by_case_id[case_1.id]["scores"]["exact_match"]["status"] == ("completed")

    assert results_by_case_id[case_2.id]["actual_output"] is None
    assert results_by_case_id[case_2.id]["scores"]["exact_match"]["status"] == ("not_applicable")
    assert results_by_case_id[case_2.id]["scores"]["exact_match"]["score"] is None
    assert results_by_case_id[case_2.id]["scores"]["overall"]["status"] == ("not_applicable")

    assert results_by_case_id[case_3.id]["actual_output"] == "answer 3"
    assert results_by_case_id[case_3.id]["scores"]["exact_match"]["status"] == ("completed")

    assert results_by_case_id[case_4.id]["actual_output"] is None
    assert results_by_case_id[case_4.id]["scores"]["exact_match"]["status"] == ("not_applicable")
    assert results_by_case_id[case_4.id]["scores"]["exact_match"]["score"] is None
    assert results_by_case_id[case_4.id]["scores"]["overall"]["status"] == ("not_applicable")

    assert scoring_service.calculate.call_count == 2


@pytest.mark.asyncio
async def test_engine_resolves_prompt_for_batch_cases(monkeypatch):
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
    ]

    run = create_run(
        model_id=model.id,
        dataset_version_id=uuid4(),
        evaluation_type=EvaluationType.TEXT,
        execution_mode="batch",
        batch_size=10,
    )

    run.configuration["prompt"] = {
        "mode": "simple",
        "instruction": "Answer using one sentence.",
    }

    db, evaluator_registry, scoring_service = create_engine_mocks(model)

    model_gateway = MagicMock()
    model_gateway.generate = AsyncMock()

    model_gateway.generate_batch = AsyncMock(
        return_value=[
            create_response("answer 1"),
            create_response("answer 2"),
        ]
    )

    engine = EvaluationEngine(
        db=db,
        model_gateway=model_gateway,
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    mock_run_summary_services(monkeypatch)

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

    mock_dataset_capabilities(
        monkeypatch,
        cases,
    )

    monkeypatch.setattr(
        engine_module.EvaluationResultService,
        "create",
        AsyncMock(),
    )

    await engine.execute(run.id)

    model_gateway.generate_batch.assert_awaited_once()

    call = model_gateway.generate_batch.await_args

    assert call.kwargs["prompts"] == [
        "Answer using one sentence.\n\nquestion 1",
        "Answer using one sentence.\n\nquestion 2",
    ]

    assert "prompt" not in call.kwargs["configuration"]
