import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.evaluation_engine.feedback_reducer_state import (
    EvaluationFeedbackReducerState,
)


@pytest.fixture
def redis():
    return AsyncMock()


@pytest.fixture
def state(redis):
    return EvaluationFeedbackReducerState(redis=redis)


def make_feedback(
    *,
    overall="Responses are generally relevant.",
    strengths=None,
    weaknesses=None,
    patterns=None,
    recommendations=None,
):
    return {
        "overall": overall,
        "strengths": strengths or ["Good relevance."],
        "weaknesses": weaknesses or ["Some responses lack detail."],
        "patterns": patterns or ["Responses are often brief."],
        "recommendations": recommendations or ["Provide more supporting detail."],
        "evaluator_feedback": [],
    }


class TestEvaluationFeedbackReducerState:
    def test_build_key(self):
        run_id = uuid4()

        key = EvaluationFeedbackReducerState.build_key(run_id)

        assert key == f"evaluation:feedback:{run_id}:state"

    def test_build_key_accepts_string(self):
        run_id = str(uuid4())

        key = EvaluationFeedbackReducerState.build_key(run_id)

        assert key == f"evaluation:feedback:{run_id}:state"

    @pytest.mark.asyncio
    async def test_get_returns_none_when_state_does_not_exist(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        redis.get = AsyncMock(return_value=None)

        result = await state.get(run_id)

        assert result is None

        redis.get.assert_awaited_once_with(EvaluationFeedbackReducerState.build_key(run_id))

    @pytest.mark.asyncio
    async def test_get_returns_decoded_state(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        payload = {
            "feedback": make_feedback(),
            "source_count": 20,
            "revision": 1,
        }

        redis.get = AsyncMock(return_value=json.dumps(payload))

        result = await state.get(run_id)

        assert result == payload

    @pytest.mark.asyncio
    async def test_get_decodes_bytes(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        payload = {
            "feedback": make_feedback(
                overall="Good relevance but weak grounding.",
            ),
            "source_count": 39,
            "revision": 2,
        }

        redis.get = AsyncMock(return_value=json.dumps(payload).encode("utf-8"))

        result = await state.get(run_id)

        assert result == payload

    @pytest.mark.asyncio
    async def test_get_returns_none_for_invalid_json(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        redis.get = AsyncMock(return_value="invalid-json")

        result = await state.get(run_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_for_non_object_json(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        redis.get = AsyncMock(return_value=json.dumps(["invalid", "state"]))

        result = await state.get(run_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_stores_structured_feedback_with_ttl(
        self,
        state,
        redis,
    ):
        run_id = uuid4()
        feedback = make_feedback(
            overall="Responses need more detail.",
        )

        redis.set = AsyncMock()

        await state.set(
            run_id,
            feedback=feedback,
            source_count=20,
            revision=1,
        )

        redis.set.assert_awaited_once()

        key, raw_payload = redis.set.await_args.args
        kwargs = redis.set.await_args.kwargs

        assert key == EvaluationFeedbackReducerState.build_key(run_id)

        payload = json.loads(raw_payload)

        assert payload == {
            "feedback": feedback,
            "source_count": 20,
            "revision": 1,
        }

        assert kwargs["ex"] == EvaluationFeedbackReducerState.DEFAULT_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_set_accepts_zero_values(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        redis.set = AsyncMock()

        await state.set(
            run_id,
            feedback=make_feedback(
                overall="Initial summary",
            ),
            source_count=0,
            revision=0,
        )

        redis.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_rejects_negative_source_count(
        self,
        state,
        redis,
    ):
        with pytest.raises(
            ValueError,
            match="source_count must be non-negative",
        ):
            await state.set(
                uuid4(),
                feedback=make_feedback(),
                source_count=-1,
                revision=0,
            )

        redis.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_rejects_negative_revision(
        self,
        state,
        redis,
    ):
        with pytest.raises(
            ValueError,
            match="revision must be non-negative",
        ):
            await state.set(
                uuid4(),
                feedback=make_feedback(),
                source_count=20,
                revision=-1,
            )

        redis.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_clear_deletes_state(
        self,
        state,
        redis,
    ):
        run_id = uuid4()

        redis.delete = AsyncMock()

        await state.clear(run_id)

        redis.delete.assert_awaited_once_with(EvaluationFeedbackReducerState.build_key(run_id))
