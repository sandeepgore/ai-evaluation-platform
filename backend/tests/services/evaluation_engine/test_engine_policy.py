from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.evaluation import EvaluationRunStatus
from app.models.evaluation.evaluation_run import EvaluationRunMode
from app.services.evaluation.evaluation_data_requirements import DataRequirement
from app.services.evaluation.run_validation import (
    EvaluationRunValidationError,
)
from app.services.evaluation_engine.engine import EvaluationEngine
from app.shared.enums import DataPolicy


def create_run(
    *,
    evaluation_type="text",
    configuration=None,
):
    return SimpleNamespace(
        id=uuid4(),
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        evaluation_type=SimpleNamespace(value=evaluation_type),
        mode=EvaluationRunMode.DEFAULT,
        configuration=configuration or {},
        status=EvaluationRunStatus.PENDING,
        total_cases=0,
        completed_cases=0,
        failed_cases=0,
    )


def create_dataset_capabilities(
    *,
    has_reference=True,
    has_context=True,
    reference_coverage=1.0,
    context_coverage=1.0,
):
    return SimpleNamespace(
        has_reference=has_reference,
        has_context=has_context,
        reference_coverage=reference_coverage,
        context_coverage=context_coverage,
    )


def create_engine():
    db = MagicMock()
    evaluator_registry = MagicMock()
    scoring_service = MagicMock()

    engine = EvaluationEngine(
        db=db,
        model_gateway=MagicMock(),
        evaluator_registry=evaluator_registry,
        scoring_service=scoring_service,
    )

    return engine


def test_effective_policy_defaults_to_strict():
    engine = create_engine()
    configuration = {}

    policy_configuration = engine.run_validation_service.resolve_data_policy(
        configuration,
    )

    assert policy_configuration.policy == DataPolicy.STRICT
    assert policy_configuration.threshold == 1.0


def test_effective_policy_resolves_partial():
    engine = create_engine()
    configuration = {
        "data_policy": {
            "type": "partial",
        },
    }

    policy_configuration = engine.run_validation_service.resolve_data_policy(
        configuration,
    )

    assert policy_configuration.policy == DataPolicy.PARTIAL
    assert policy_configuration.threshold == 1.0


def test_effective_policy_resolves_threshold():
    engine = create_engine()
    configuration = {
        "data_policy": {
            "type": "threshold",
            "threshold": 0.5,
        },
    }

    policy_configuration = engine.run_validation_service.resolve_data_policy(
        configuration,
    )

    assert policy_configuration.policy == DataPolicy.THRESHOLD
    assert policy_configuration.threshold == 0.5


def test_strict_policy_rejects_partial_reference_coverage():
    engine = create_engine()
    capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    with pytest.raises(EvaluationRunValidationError):
        engine.run_validation_service.validate_policy(
            dataset_capabilities=capabilities,
            requirements=[
                DataRequirement.REFERENCE,
            ],
            policy=DataPolicy.STRICT,
            threshold=1.0,
        )


def test_partial_policy_allows_partial_reference_coverage():
    engine = create_engine()
    capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    engine.run_validation_service.validate_policy(
        dataset_capabilities=capabilities,
        requirements=[
            DataRequirement.REFERENCE,
        ],
        policy=DataPolicy.PARTIAL,
        threshold=1.0,
    )


def test_threshold_policy_allows_coverage_at_threshold():
    engine = create_engine()
    capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    engine.run_validation_service.validate_policy(
        dataset_capabilities=capabilities,
        requirements=[
            DataRequirement.REFERENCE,
        ],
        policy=DataPolicy.THRESHOLD,
        threshold=0.5,
    )


def test_threshold_policy_rejects_coverage_below_threshold():
    engine = create_engine()
    capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    with pytest.raises(EvaluationRunValidationError):
        engine.run_validation_service.validate_policy(
            dataset_capabilities=capabilities,
            requirements=[
                DataRequirement.REFERENCE,
            ],
            policy=DataPolicy.THRESHOLD,
            threshold=0.8,
        )


def test_default_evaluators_receive_effective_policy():
    engine = create_engine()
    run = create_run(
        evaluation_type="text",
        configuration={},
    )
    dataset_capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    capabilities = engine._get_evaluation_capabilities(
        run=run,
        dataset_capabilities=dataset_capabilities,
        llm_available=False,
    )

    # Mock return values matching resolved default evaluators count
    engine.applicability_service.validate = MagicMock(
        side_effect=lambda names, capabilities, defer_data_requirements=False: names
    )

    engine._get_evaluators(
        run,
        capabilities,
        dataset_capabilities,
        policy=DataPolicy.PARTIAL,
        policy_threshold=1.0,
    )

    validated_names = [
        call.args[0] for call in engine.applicability_service.validate.call_args_list
    ]

    assert validated_names
    evaluator_names = validated_names[0]
    assert "exact_match" in evaluator_names
    assert "f1" in evaluator_names


def test_strict_policy_prevents_default_reference_evaluators_on_partial_coverage():
    engine = create_engine()
    run = create_run(
        evaluation_type="text",
        configuration={},
    )
    dataset_capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    capabilities = engine._get_evaluation_capabilities(
        run=run,
        dataset_capabilities=dataset_capabilities,
        llm_available=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        engine._get_evaluators(
            run,
            capabilities,
            dataset_capabilities,
            policy=DataPolicy.STRICT,
            policy_threshold=1.0,
        )

    assert exc_info.value.status_code == 400
    assert "evaluator" in str(exc_info.value.detail).lower()


def test_threshold_policy_is_passed_to_default_evaluator_resolution():
    engine = create_engine()
    run = create_run(
        evaluation_type="text",
        configuration={},
    )
    dataset_capabilities = create_dataset_capabilities(
        has_reference=True,
        reference_coverage=0.5,
    )

    capabilities = engine._get_evaluation_capabilities(
        run=run,
        dataset_capabilities=dataset_capabilities,
        llm_available=False,
    )

    engine.applicability_service.validate = MagicMock(
        side_effect=lambda names, capabilities, defer_data_requirements=False: names
    )

    engine._get_evaluators(
        run,
        capabilities,
        dataset_capabilities,
        policy=DataPolicy.THRESHOLD,
        policy_threshold=0.5,
    )

    validated_names = engine.applicability_service.validate.call_args.args[0]

    assert "exact_match" in validated_names
    assert "f1" in validated_names


def test_get_evaluation_capabilities_includes_llm_availability():
    engine = create_engine()
    run = create_run(
        evaluation_type="text",
    )
    dataset_capabilities = create_dataset_capabilities()

    capabilities = engine._get_evaluation_capabilities(
        run=run,
        dataset_capabilities=dataset_capabilities,
        llm_available=True,
    )

    assert capabilities.llm_available is True


def test_get_evaluation_capabilities_rejects_non_boolean_llm_availability():
    engine = create_engine()
    run = create_run(
        evaluation_type="text",
    )
    dataset_capabilities = create_dataset_capabilities()

    with pytest.raises(HTTPException) as exc_info:
        engine._get_evaluation_capabilities(
            run=run,
            dataset_capabilities=dataset_capabilities,
            llm_available="yes",
        )

    assert exc_info.value.status_code == 400
    assert "'llm_available' must be a boolean." in exc_info.value.detail


@pytest.mark.asyncio
async def test_policy_violation_prevents_model_execution():
    engine = create_engine()
    run = create_run(
        evaluation_type="text",
        configuration={
            "data_policy": {
                "type": "strict",
            },
        },
    )

    # Mock DB query for active model
    mock_model = SimpleNamespace(id=run.model_id, is_active=True, configuration={})
    mock_db_result = MagicMock()
    mock_db_result.scalar_one_or_none.return_value = mock_model
    engine.db.execute = AsyncMock(return_value=mock_db_result)

    engine.run_validation_service.resolve_data_policy = MagicMock(
        return_value=SimpleNamespace(
            policy=DataPolicy.STRICT,
            threshold=1.0,
        ),
    )

    engine.run_validation_service.validate_policy = MagicMock(
        side_effect=EvaluationRunValidationError(
            "Evaluation run violates the configured data policy."
        ),
    )

    engine.model_gateway.generate = AsyncMock()

    from app.services.evaluation_engine import engine as engine_module

    engine_module.EvaluationRunService.get_by_id = AsyncMock(
        return_value=run,
    )
    engine_module.DatasetCapabilityService.analyze_dataset_version = AsyncMock(
        return_value=create_dataset_capabilities(has_reference=True, reference_coverage=0.5)
    )

    with pytest.raises(HTTPException) as exc_info:
        await engine.execute(run.id)

    assert exc_info.value.status_code == 400
    engine.model_gateway.generate.assert_not_awaited()
