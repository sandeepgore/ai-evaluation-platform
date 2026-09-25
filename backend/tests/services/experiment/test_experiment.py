from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.experiment.experiment import ExperimentCreate
from app.services.experiment.experiment import ExperimentService
from app.models.evaluation import EvaluationRunStatus
from app.schemas.experiment.snapshot import ExperimentSnapshotCreate
from app.services.evaluation.evaluation import EvaluationRunService
from app.services.evaluation_engine.summary_persistence import (
    EvaluationSummaryPersistenceService,
)


@pytest.mark.asyncio
async def test_create_experiment():
    db = AsyncMock()
    db.add = MagicMock()

    data = ExperimentCreate(
        name="Test Experiment",
        description="Test experiment description",
    )

    service = ExperimentService(db)

    experiment = await service.create(data)

    assert experiment.name == data.name
    assert experiment.description == data.description

    db.add.assert_called_once_with(experiment)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(experiment)


@pytest.mark.asyncio
async def test_get_by_id_returns_experiment():
    experiment = MagicMock()
    experiment.id = uuid4()

    result = MagicMock()
    result.scalar_one_or_none.return_value = experiment

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = result

    service = ExperimentService(db)

    returned = await service.get_by_id(experiment.id)

    assert returned == experiment
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_experiment_not_found():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = result

    service = ExperimentService(db)

    returned = await service.get_by_id(uuid4())

    assert returned is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_recent_experiments():
    experiment_one = MagicMock()
    experiment_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        experiment_one,
        experiment_two,
    ]

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = result

    service = ExperimentService(db)

    experiments = await service.list()

    assert experiments == [
        experiment_one,
        experiment_two,
    ]

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_all_experiments():
    experiment_one = MagicMock()
    experiment_two = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        experiment_one,
        experiment_two,
    ]

    db = AsyncMock()
    db.add = MagicMock()
    db.execute.return_value = result

    service = ExperimentService(db)

    experiments = await service.list(scope="all")

    assert experiments == [
        experiment_one,
        experiment_two,
    ]

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_rejects_invalid_scope():
    db = AsyncMock()
    db.add = MagicMock()

    service = ExperimentService(db)

    with pytest.raises(
        ValueError,
        match="Invalid experiment scope",
    ):
        await service.list(scope="invalid")

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_experiment():
    experiment = MagicMock()
    experiment.is_active = True

    db = AsyncMock()
    db.add = MagicMock()

    service = ExperimentService(db)

    await service.delete(experiment)

    assert experiment.is_active is False
    db.delete.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_snapshot_with_single_run(monkeypatch):
    experiment = MagicMock()
    experiment.id = uuid4()

    run_id = uuid4()
    run = MagicMock()
    run.id = run_id
    run.name = "Baseline Run"
    run.model_id = uuid4()
    run.dataset_version_id = uuid4()
    run.status = EvaluationRunStatus.COMPLETED
    run.total_cases = 100
    run.completed_cases = 100
    run.failed_cases = 0
    run.duration_ms = 12000

    summary = MagicMock()
    summary.overall_score = 0.82
    summary.metrics = {
        "relevance": 0.91,
        "faithfulness": 0.74,
    }
    summary.performance = {}
    summary.feedback = {}
    summary.summary_metadata = {}

    async def mock_get_run(db, requested_run_id):
        assert requested_run_id == run_id
        return run

    async def mock_get_summary(db, requested_run_id):
        assert requested_run_id == run_id
        return summary

    monkeypatch.setattr(
        EvaluationRunService,
        "get_by_id",
        mock_get_run,
    )

    monkeypatch.setattr(
        EvaluationSummaryPersistenceService,
        "get",
        mock_get_summary,
    )

    db = AsyncMock()
    db.add = MagicMock()

    service = ExperimentService(db)

    snapshot = await service.create_snapshot(
        experiment,
        ExperimentSnapshotCreate(
            run_ids=[run_id],
        ),
    )

    assert snapshot.experiment_id == experiment.id
    assert snapshot.run_ids == [str(run_id)]

    assert snapshot.run_results[str(run_id)]["run"]["name"] == "Baseline Run"
    assert snapshot.run_results[str(run_id)]["summary"]["overall_score"] == 0.82

    assert snapshot.comparison == {}

    assert snapshot.calculation_version == 1

    db.add.assert_called_once_with(snapshot)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(snapshot)


@pytest.mark.asyncio
async def test_create_snapshot_compares_candidate_against_first_run(
    monkeypatch,
):
    experiment = MagicMock()
    experiment.id = uuid4()

    baseline_id = uuid4()
    candidate_id = uuid4()

    baseline_run = MagicMock(
        id=baseline_id,
        name="Baseline",
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        status=EvaluationRunStatus.COMPLETED,
        total_cases=100,
        completed_cases=100,
        failed_cases=0,
        duration_ms=10000,
    )

    candidate_run = MagicMock(
        id=candidate_id,
        name="Candidate",
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        status=EvaluationRunStatus.COMPLETED,
        total_cases=100,
        completed_cases=100,
        failed_cases=0,
        duration_ms=8000,
    )

    runs = {
        baseline_id: baseline_run,
        candidate_id: candidate_run,
    }

    summaries = {
        baseline_id: MagicMock(
            overall_score=0.82,
            metrics={
                "relevance": 0.91,
                "faithfulness": 0.74,
            },
            performance={},
            feedback={},
            summary_metadata={},
        ),
        candidate_id: MagicMock(
            overall_score=0.87,
            metrics={
                "relevance": 0.93,
                "faithfulness": 0.78,
            },
            performance={},
            feedback={},
            summary_metadata={},
        ),
    }

    async def mock_get_run(db, run_id):
        return runs.get(run_id)

    async def mock_get_summary(db, run_id):
        return summaries.get(run_id)

    monkeypatch.setattr(
        EvaluationRunService,
        "get_by_id",
        mock_get_run,
    )

    monkeypatch.setattr(
        EvaluationSummaryPersistenceService,
        "get",
        mock_get_summary,
    )

    db = AsyncMock()
    db.add = MagicMock()

    service = ExperimentService(db)

    snapshot = await service.create_snapshot(
        experiment,
        ExperimentSnapshotCreate(
            run_ids=[
                baseline_id,
                candidate_id,
            ],
        ),
    )

    comparison = snapshot.comparison

    assert comparison["overall_score"]["baseline"] == 0.82
    assert comparison["overall_score"]["candidate"] == 0.87
    assert comparison["overall_score"]["delta"] == pytest.approx(0.05)

    assert comparison["relevance"]["baseline"] == 0.91
    assert comparison["relevance"]["candidate"] == 0.93
    assert comparison["relevance"]["delta"] == pytest.approx(0.02)

    assert comparison["faithfulness"]["baseline"] == 0.74
    assert comparison["faithfulness"]["candidate"] == 0.78
    assert comparison["faithfulness"]["delta"] == pytest.approx(0.04)


@pytest.mark.asyncio
async def test_create_snapshot_rejects_missing_run(monkeypatch):
    experiment = MagicMock()
    experiment.id = uuid4()

    missing_run_id = uuid4()

    async def mock_get_run(db, run_id):
        return None

    monkeypatch.setattr(
        EvaluationRunService,
        "get_by_id",
        mock_get_run,
    )

    db = AsyncMock()
    db.add = MagicMock()
    service = ExperimentService(db)

    with pytest.raises(
        ValueError,
        match="Evaluation run not found",
    ):
        await service.create_snapshot(
            experiment,
            ExperimentSnapshotCreate(
                run_ids=[missing_run_id],
            ),
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_snapshot_rejects_missing_summary(monkeypatch):
    experiment = MagicMock()
    experiment.id = uuid4()

    run_id = uuid4()

    run = MagicMock(
        id=run_id,
        name="Run",
        model_id=uuid4(),
        dataset_version_id=uuid4(),
        status=EvaluationRunStatus.COMPLETED,
        total_cases=10,
        completed_cases=10,
        failed_cases=0,
        duration_ms=1000,
    )

    async def mock_get_run(db, requested_run_id):
        return run

    async def mock_get_summary(db, requested_run_id):
        return None

    monkeypatch.setattr(
        EvaluationRunService,
        "get_by_id",
        mock_get_run,
    )

    monkeypatch.setattr(
        EvaluationSummaryPersistenceService,
        "get",
        mock_get_summary,
    )

    db = AsyncMock()
    db.add = MagicMock()
    service = ExperimentService(db)

    with pytest.raises(
        ValueError,
        match="Evaluation summary not found",
    ):
        await service.create_snapshot(
            experiment,
            ExperimentSnapshotCreate(
                run_ids=[run_id],
            ),
        )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
