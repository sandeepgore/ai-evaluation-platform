import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.evaluation_engine.feedback import (
    EvaluationRunFeedbackService,
)


def make_result(
    *,
    status: str = "completed",
    feedback=None,
    is_active: bool = True,
):
    return SimpleNamespace(
        status=status,
        feedback=feedback,
        is_active=is_active,
    )


def make_db(results):
    db = MagicMock()

    scalars = MagicMock()
    scalars.all.return_value = results

    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars

    db.execute = AsyncMock(return_value=execute_result)

    return db


class TestEvaluationRunFeedbackService:
    def test_normalize_feedback(self):
        result = EvaluationRunFeedbackService._normalize_feedback(
            "  exact_match:   response   differs \n from reference  "
        )

        assert result == "exact_match: response differs from reference"

    def test_no_results_returns_none(self):
        db = make_db([])

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is None

    def test_completed_results_without_feedback_returns_none(self):
        db = make_db(
            [
                make_result(feedback=None),
                make_result(feedback=""),
                make_result(feedback="   "),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is None

    def test_failed_cases_without_feedback_returns_failure_summary(self):
        db = make_db(
            [
                make_result(status="completed"),
                make_result(status="failed"),
                make_result(status="failed"),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result == (
            "Evaluation completed with 2 failed case(s). "
            "No evaluator feedback was available from the "
            "1 completed case(s)."
        )

    def test_completed_feedback_generates_summary(self):
        db = make_db(
            [
                make_result(feedback="exact_match: response differs from reference"),
                make_result(feedback="f1: partial token overlap"),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None
        assert "Evaluator feedback was collected from 2 completed case result(s)." in result
        assert "- exact_match: response differs from reference" in result
        assert "- f1: partial token overlap" in result

    def test_duplicate_feedback_is_counted(self):
        db = make_db(
            [
                make_result(feedback="exact_match: response differs from reference"),
                make_result(feedback="exact_match: response differs from reference"),
                make_result(feedback="f1: partial token overlap"),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None
        assert ("- exact_match: response differs from reference (observed 2 times)") in result

    def test_feedback_whitespace_is_normalized(self):
        db = make_db(
            [make_result(feedback=("  exact_match:   response   differs\n from reference  "))]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None
        assert "- exact_match: response differs from reference" in result

    def test_non_string_feedback_is_ignored(self):
        db = make_db(
            [
                make_result(feedback=None),
                make_result(feedback=123),
                make_result(feedback={"metric": "f1"}),
                make_result(feedback=["feedback"]),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is None

    def test_non_completed_results_are_ignored(self):
        db = make_db(
            [
                make_result(
                    status="failed",
                    feedback="exact_match: failed result",
                ),
                make_result(
                    status="running",
                    feedback="f1: running result",
                ),
                make_result(
                    status="pending",
                    feedback="bleu: pending result",
                ),
                make_result(
                    status="completed",
                    feedback="rouge: completed result",
                ),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None
        assert "- rouge: completed result" in result
        assert "failed result" not in result
        assert "running result" not in result
        assert "pending result" not in result

    def test_inactive_results_are_filtered_by_query(self):
        db = make_db(
            [
                make_result(
                    feedback="exact_match: active result",
                )
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None
        assert "active result" in result
        db.execute.assert_awaited_once()

    def test_maximum_five_feedback_items(self):
        db = make_db([make_result(feedback=f"metric_{i}: unique feedback") for i in range(10)])

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None

        feedback_lines = [line for line in result.splitlines() if line.startswith("- ")]

        assert len(feedback_lines) == 5

    def test_feedback_ordering_is_deterministic(self):
        db = make_db(
            [
                make_result(feedback="z_metric: feedback"),
                make_result(feedback="a_metric: feedback"),
                make_result(feedback="m_metric: feedback"),
                make_result(feedback="a_metric: feedback"),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None

        lines = [line for line in result.splitlines() if line.startswith("- ")]

        assert lines == [
            "- a_metric: feedback (observed 2 times)",
            "- m_metric: feedback",
            "- z_metric: feedback",
        ]

    def test_failed_and_completed_results_are_combined(self):
        db = make_db(
            [
                make_result(
                    status="completed",
                    feedback="f1: partial token overlap",
                ),
                make_result(
                    status="completed",
                    feedback="exact_match: response differs",
                ),
                make_result(status="failed"),
            ]
        )

        result = asyncio.run(EvaluationRunFeedbackService.generate(db, "run-id"))

        assert result is not None
        assert "1 case(s) failed during evaluation." in result
        assert ("Evaluator feedback was collected from 2 completed case result(s).") in result
