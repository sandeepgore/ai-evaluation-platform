from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.evaluation_engine.summary_persistence import (
    EvaluationSummaryPersistenceService,
)


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDB:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = None
        self.flushed = False
        self.deleted = None

    async def execute(self, statement):
        return FakeResult(self.existing)

    def add(self, value):
        self.added = value

    async def flush(self):
        self.flushed = True

    async def delete(self, value):
        self.deleted = value


def make_summary():
    return SimpleNamespace(
        overall_score=0.82,
        metrics={
            "relevance": 0.9,
            "f1": 0.74,
        },
        performance={
            "total_cases": 10,
            "completed_cases": 10,
            "failed_cases": 0,
        },
        feedback={
            "overall": "Strong overall performance.",
            "strengths": ["Good relevance"],
            "weaknesses": ["F1 can improve"],
            "patterns": [],
            "recommendations": ["Improve answer alignment"],
        },
        metadata={
            "summary_model": "llama3.2:3b",
            "summary_provider": "ollama",
        },
    )


class TestEvaluationSummaryPersistenceService:
    @pytest.mark.asyncio
    async def test_get_returns_existing_summary(self):
        evaluation_run_id = uuid4()
        existing = SimpleNamespace(
            evaluation_run_id=evaluation_run_id,
        )

        db = FakeDB(existing=existing)

        result = await EvaluationSummaryPersistenceService.get(
            db,
            evaluation_run_id,
        )

        assert result is existing

    @pytest.mark.asyncio
    async def test_get_returns_none_when_summary_does_not_exist(self):
        db = FakeDB(existing=None)

        result = await EvaluationSummaryPersistenceService.get(
            db,
            uuid4(),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_save_creates_new_summary(self):
        evaluation_run_id = uuid4()
        db = FakeDB(existing=None)

        summary = make_summary()

        result = await EvaluationSummaryPersistenceService.save(
            db,
            evaluation_run_id,
            summary.__dict__,
        )

        assert result is db.added
        assert result.evaluation_run_id == evaluation_run_id
        assert result.overall_score == 0.82
        assert result.metrics == summary.metrics
        assert result.performance == summary.performance
        assert result.feedback == summary.feedback
        assert result.summary_metadata == summary.metadata

        assert db.flushed is True

    @pytest.mark.asyncio
    async def test_save_updates_existing_summary(self):
        evaluation_run_id = uuid4()

        existing = SimpleNamespace(
            evaluation_run_id=evaluation_run_id,
            overall_score=0.2,
            metrics={},
            performance={},
            feedback={},
            summary_metadata={},
        )

        db = FakeDB(existing=existing)

        summary = make_summary()

        result = await EvaluationSummaryPersistenceService.save(
            db,
            evaluation_run_id,
            summary.__dict__,
        )

        assert result is existing
        assert db.added is None

        assert existing.overall_score == 0.82
        assert existing.metrics == summary.metrics
        assert existing.performance == summary.performance
        assert existing.feedback == summary.feedback
        assert existing.summary_metadata == summary.metadata

        assert db.flushed is True

    @pytest.mark.asyncio
    async def test_delete_does_nothing_when_summary_does_not_exist(self):
        db = FakeDB(existing=None)

        await EvaluationSummaryPersistenceService.delete(
            db,
            uuid4(),
        )

        assert db.deleted is None

    @pytest.mark.asyncio
    async def test_delete_removes_existing_summary(self):
        existing = SimpleNamespace(
            evaluation_run_id=uuid4(),
        )

        db = FakeDB(existing=existing)

        await EvaluationSummaryPersistenceService.delete(
            db,
            existing.evaluation_run_id,
        )

        assert db.deleted is existing
        assert db.flushed is True
