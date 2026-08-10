import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.evaluation_engine.summary import (
    EvaluationRunSummaryService,
)


@pytest.mark.asyncio
async def test_summary_calculates_metric_and_overall_averages():
    run_id = uuid4()

    results = [
        SimpleNamespace(
            evaluation_run_id=run_id,
            status="completed",
            is_active=True,
            scores={
                "exact_match": {"score": 1.0},
                "f1": {"score": 0.8},
                "overall": {"score": 0.9},
            },
        ),
        SimpleNamespace(
            evaluation_run_id=run_id,
            status="completed",
            is_active=True,
            scores={
                "exact_match": {"score": 0.0},
                "f1": {"score": 0.6},
                "overall": {"score": 0.3},
            },
        ),
        SimpleNamespace(
            evaluation_run_id=run_id,
            status="failed",
            is_active=True,
            scores={},
        ),
    ]

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: results
            )
        )
    )

    summary = await EvaluationRunSummaryService.calculate(
        db,
        run_id,
    )

    assert summary["overall_score"] == pytest.approx(0.6)

    assert summary["metrics"]["exact_match"] == pytest.approx(0.5)

    assert summary["metrics"]["f1"] == pytest.approx(0.7)

    assert summary["total_results"] == 3
    assert summary["completed_cases"] == 2
    assert summary["failed_cases"] == 1


@pytest.mark.asyncio
async def test_summary_returns_zero_when_no_results():
    run_id = uuid4()

    db = MagicMock()

    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: []
            )
        )
    )

    summary = await EvaluationRunSummaryService.calculate(
        db,
        run_id,
    )

    assert summary["overall_score"] == 0.0
    assert summary["metrics"] == {}
    assert summary["total_results"] == 0
    assert summary["completed_cases"] == 0
    assert summary["failed_cases"] == 0