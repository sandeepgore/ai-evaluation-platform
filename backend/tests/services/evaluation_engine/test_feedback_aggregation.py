from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.evaluation.summary import EvaluationRunFeedbackResponse
from app.services.evaluation_engine.feedback_aggregation import (
    EvaluationFeedbackAggregationService,
)


def make_feedback(
    *,
    overall="Responses are generally relevant.",
    strengths=None,
    weaknesses=None,
    patterns=None,
    recommendations=None,
):
    return EvaluationRunFeedbackResponse(
        overall=overall,
        strengths=strengths or ["Good relevance."],
        weaknesses=weaknesses or ["Some responses lack detail."],
        patterns=patterns or ["Responses are often brief."],
        recommendations=recommendations or ["Provide more supporting detail."],
        evaluator_feedback=[],
    )


def make_buffer(
    *,
    size=0,
    pop_window=None,
):
    buffer = AsyncMock()

    buffer.size = AsyncMock(return_value=size)

    if pop_window is None:
        buffer.pop_window = AsyncMock(return_value=[])

    else:
        buffer.pop_window = AsyncMock(
            return_value=pop_window,
        )

    buffer.add = AsyncMock()
    buffer.prepend = AsyncMock()
    buffer.clear = AsyncMock()

    return buffer


def make_state(
    *,
    current_state=None,
):
    state = AsyncMock()

    state.get = AsyncMock(
        return_value=current_state,
    )

    state.set = AsyncMock()
    state.clear = AsyncMock()

    return state


def make_reducer(
    *,
    feedback=None,
):
    reducer = AsyncMock()

    reducer.reduce = AsyncMock(
        return_value=feedback or make_feedback(),
    )

    return reducer


def make_service(
    *,
    buffer=None,
    state=None,
    reducer=None,
    window_size=20,
):
    return EvaluationFeedbackAggregationService(
        redis=AsyncMock(),
        reducer=reducer or make_reducer(),
        buffer=buffer or make_buffer(),
        state=state or make_state(),
        window_size=window_size,
    )


class TestEvaluationFeedbackAggregationService:
    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def test_default_window_size(self):
        service = make_service()

        assert service.window_size == 20
        assert service.reducer_input_size == 19

    def test_custom_window_size(self):
        service = make_service(
            window_size=10,
        )

        assert service.window_size == 10
        assert service.reducer_input_size == 9

    def test_window_size_must_be_at_least_two(self):
        with pytest.raises(
            ValueError,
            match="window_size must be at least 2",
        ):
            make_service(window_size=1)

    def test_build_lock_key(self):
        run_id = uuid4()

        key = EvaluationFeedbackAggregationService.build_lock_key(
            run_id,
        )

        assert key == (f"evaluation:feedback:{run_id}:reduce-lock")

    def test_build_lock_key_accepts_string(self):
        key = EvaluationFeedbackAggregationService.build_lock_key(
            "run-id",
        )

        assert key == ("evaluation:feedback:run-id:reduce-lock")

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def test_state_feedback_returns_none_when_state_missing(self):
        service = make_service()

        assert service._state_feedback(None) is None

    def test_state_feedback_restores_structured_feedback(self):
        service = make_service()

        feedback = make_feedback()

        state = {
            "feedback": feedback.model_dump(),
            "source_count": 20,
            "revision": 1,
        }

        result = service._state_feedback(state)

        assert result == feedback

    def test_state_feedback_discards_raw_evaluator_feedback(self):
        service = make_service()

        state = {
            "feedback": {
                **make_feedback().model_dump(),
                "evaluator_feedback": [
                    "raw feedback should not survive",
                ],
            },
            "source_count": 20,
            "revision": 1,
        }

        result = service._state_feedback(state)

        assert result is not None
        assert result.evaluator_feedback == []

    def test_state_source_count_defaults_to_zero(self):
        service = make_service()

        assert service._state_source_count(None) == 0
        assert service._state_source_count({}) == 0

    def test_state_source_count_reads_valid_value(self):
        service = make_service()

        assert (
            service._state_source_count(
                {
                    "source_count": 39,
                }
            )
            == 39
        )

    def test_state_source_count_rejects_invalid_value(self):
        service = make_service()

        assert (
            service._state_source_count(
                {
                    "source_count": "39",
                }
            )
            == 0
        )

    def test_state_revision_defaults_to_zero(self):
        service = make_service()

        assert service._state_revision(None) == 0
        assert service._state_revision({}) == 0

    def test_state_revision_reads_valid_value(self):
        service = make_service()

        assert (
            service._state_revision(
                {
                    "revision": 4,
                }
            )
            == 4
        )

    # ------------------------------------------------------------------
    # Accept
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_accept_adds_feedback_to_buffer(
        self,
    ):
        run_id = uuid4()
        result_id = uuid4()

        buffer = make_buffer(size=0)

        service = make_service(
            buffer=buffer,
        )

        result = await service.accept(
            run_id,
            result_id,
            "Useful feedback.",
        )

        buffer.add.assert_awaited_once_with(
            run_id,
            result_id,
            "Useful feedback.",
        )

        assert result["reduced"] is False

    @pytest.mark.asyncio
    async def test_accept_ignores_empty_feedback(
        self,
    ):
        run_id = uuid4()
        result_id = uuid4()

        buffer = make_buffer(size=0)

        service = make_service(
            buffer=buffer,
        )

        await service.accept(
            run_id,
            result_id,
            "   ",
        )

        buffer.add.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_accept_ignores_non_string_feedback(
        self,
    ):
        run_id = uuid4()
        result_id = uuid4()

        buffer = make_buffer(size=0)

        service = make_service(
            buffer=buffer,
        )

        await service.accept(
            run_id,
            result_id,
            None,
        )

        buffer.add.assert_not_awaited()

    # ------------------------------------------------------------------
    # Threshold behavior
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_first_reduction_requires_twenty_items(
        self,
    ):
        run_id = uuid4()

        buffer = make_buffer(
            size=19,
        )

        reducer = make_reducer()

        service = make_service(
            buffer=buffer,
            reducer=reducer,
        )

        result = await service.reduce_if_ready(
            run_id,
        )

        assert result["reduced"] is False
        assert result["reason"] == "threshold_not_reached"
        assert result["pending"] == 19
        assert result["threshold"] == 20

        buffer.pop_window.assert_not_awaited()
        reducer.reduce.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_first_reduction_consumes_twenty_items(
        self,
    ):
        run_id = uuid4()

        items = [
            {
                "id": str(uuid4()),
                "feedback": f"feedback {index}",
            }
            for index in range(20)
        ]

        buffer = make_buffer(
            size=20,
            pop_window=items,
        )

        state = make_state(
            current_state=None,
        )

        reducer = make_reducer()

        service = make_service(
            buffer=buffer,
            state=state,
            reducer=reducer,
        )

        result = await service.reduce_if_ready(
            run_id,
        )

        assert result["reduced"] is True
        assert result["source_count"] == 20
        assert result["revision"] == 1

        buffer.pop_window.assert_awaited_once_with(
            run_id,
            20,
        )

        reducer.reduce.assert_awaited_once_with(
            current_feedback=None,
            feedback_items=items,
        )

        state.set.assert_awaited_once()

        kwargs = state.set.await_args.kwargs

        assert kwargs["source_count"] == 20
        assert kwargs["revision"] == 1

    @pytest.mark.asyncio
    async def test_subsequent_reduction_requires_nineteen_items(
        self,
    ):
        run_id = uuid4()

        previous_feedback = make_feedback()

        state = make_state(
            current_state={
                "feedback": previous_feedback.model_dump(),
                "source_count": 20,
                "revision": 1,
            }
        )

        buffer = make_buffer(
            size=18,
        )

        service = make_service(
            buffer=buffer,
            state=state,
        )

        result = await service.reduce_if_ready(
            run_id,
        )

        assert result["reduced"] is False
        assert result["reason"] == "threshold_not_reached"
        assert result["pending"] == 18
        assert result["threshold"] == 19

    @pytest.mark.asyncio
    async def test_subsequent_reduction_uses_previous_feedback_plus_nineteen_items(
        self,
    ):
        run_id = uuid4()

        previous_feedback = make_feedback()

        items = [
            {
                "id": str(uuid4()),
                "feedback": f"feedback {index}",
            }
            for index in range(19)
        ]

        new_feedback = make_feedback(
            overall="The latest feedback indicates good relevance with recurring completeness issues.",
        )

        buffer = make_buffer(
            size=19,
            pop_window=items,
        )

        state = make_state(
            current_state={
                "feedback": previous_feedback.model_dump(),
                "source_count": 20,
                "revision": 1,
            }
        )

        reducer = make_reducer(
            feedback=new_feedback,
        )

        service = make_service(
            buffer=buffer,
            state=state,
            reducer=reducer,
        )

        result = await service.reduce_if_ready(
            run_id,
        )

        assert result["reduced"] is True
        assert result["source_count"] == 39
        assert result["revision"] == 2
        assert result["feedback"] == new_feedback.model_dump()

        buffer.pop_window.assert_awaited_once_with(
            run_id,
            19,
        )

        reducer.reduce.assert_awaited_once_with(
            current_feedback=previous_feedback,
            feedback_items=items,
        )

        state.set.assert_awaited_once_with(
            run_id,
            feedback=new_feedback.model_dump(),
            source_count=39,
            revision=2,
        )

    # ------------------------------------------------------------------
    # Insufficient pop / recovery
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_reduction_restores_items_when_pop_returns_too_few(
        self,
    ):
        run_id = uuid4()

        items = [
            {
                "id": str(uuid4()),
                "feedback": "feedback",
            }
            for _ in range(5)
        ]

        buffer = make_buffer(
            size=20,
            pop_window=items,
        )

        service = make_service(
            buffer=buffer,
        )

        result = await service.reduce_if_ready(
            run_id,
        )

        assert result["reduced"] is False
        assert result["reason"] == "insufficient_items"

        buffer.prepend.assert_awaited_once_with(
            run_id,
            items,
        )

    @pytest.mark.asyncio
    async def test_reducer_failure_restores_items(
        self,
    ):
        run_id = uuid4()

        items = [
            {
                "id": str(uuid4()),
                "feedback": "feedback",
            }
            for _ in range(20)
        ]

        buffer = make_buffer(
            size=20,
            pop_window=items,
        )

        reducer = make_reducer()

        reducer.reduce.side_effect = RuntimeError("LLM unavailable")

        service = make_service(
            buffer=buffer,
            reducer=reducer,
        )

        with pytest.raises(
            RuntimeError,
            match="LLM unavailable",
        ):
            await service.reduce_if_ready(
                run_id,
            )

        buffer.prepend.assert_awaited_once_with(
            run_id,
            items,
        )

    # ------------------------------------------------------------------
    # Source count / revision progression
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_rolling_reduction_progresses_source_count(
        self,
    ):
        run_id = uuid4()

        first_items = [
            {
                "id": str(uuid4()),
                "feedback": f"feedback {index}",
            }
            for index in range(20)
        ]

        second_items = [
            {
                "id": str(uuid4()),
                "feedback": f"feedback {index}",
            }
            for index in range(19)
        ]

        first_feedback = make_feedback(
            overall="First reduction.",
        )

        second_feedback = make_feedback(
            overall="Second reduction.",
        )

        buffer = AsyncMock()

        buffer.add = AsyncMock()
        buffer.prepend = AsyncMock()
        buffer.clear = AsyncMock()

        buffer.size = AsyncMock(
            side_effect=[
                20,
                19,
            ]
        )

        buffer.pop_window = AsyncMock(
            side_effect=[
                first_items,
                second_items,
            ]
        )

        state = AsyncMock()

        state.get = AsyncMock(
            side_effect=[
                None,
                {
                    "feedback": first_feedback.model_dump(),
                    "source_count": 20,
                    "revision": 1,
                },
            ]
        )

        state.set = AsyncMock()
        state.clear = AsyncMock()

        reducer = AsyncMock()

        reducer.reduce = AsyncMock(
            side_effect=[
                first_feedback,
                second_feedback,
            ]
        )

        service = make_service(
            buffer=buffer,
            state=state,
            reducer=reducer,
        )

        first = await service.reduce_if_ready(
            run_id,
        )

        second = await service.reduce_if_ready(
            run_id,
        )

        assert first["source_count"] == 20
        assert first["revision"] == 1

        assert second["source_count"] == 39
        assert second["revision"] == 2

        assert state.set.await_count == 2

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_finalize_with_no_remaining_feedback_keeps_current_state(
        self,
    ):
        run_id = uuid4()

        feedback = make_feedback()

        state = make_state(
            current_state={
                "feedback": feedback.model_dump(),
                "source_count": 39,
                "revision": 2,
            }
        )

        buffer = make_buffer(
            size=0,
        )

        reducer = make_reducer()

        service = make_service(
            buffer=buffer,
            state=state,
            reducer=reducer,
        )

        result = await service.finalize(
            run_id,
        )

        assert result["finalized"] is True
        assert result["feedback"] == feedback.model_dump()
        assert result["source_count"] == 39
        assert result["revision"] == 2

        reducer.reduce.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_finalize_reduces_remaining_feedback(
        self,
    ):
        run_id = uuid4()

        previous_feedback = make_feedback()

        remaining = [
            {
                "id": str(uuid4()),
                "feedback": f"remaining feedback {index}",
            }
            for index in range(4)
        ]

        final_feedback = make_feedback(
            overall="Final accumulated feedback.",
        )

        buffer = make_buffer(
            size=4,
            pop_window=remaining,
        )

        state = make_state(
            current_state={
                "feedback": previous_feedback.model_dump(),
                "source_count": 96,
                "revision": 5,
            }
        )

        reducer = make_reducer(
            feedback=final_feedback,
        )

        service = make_service(
            buffer=buffer,
            state=state,
            reducer=reducer,
        )

        result = await service.finalize(
            run_id,
        )

        assert result["finalized"] is True
        assert result["feedback"] == final_feedback.model_dump()
        assert result["source_count"] == 100
        assert result["revision"] == 6

        reducer.reduce.assert_awaited_once_with(
            current_feedback=previous_feedback,
            feedback_items=remaining,
        )

        state.set.assert_awaited_once_with(
            run_id,
            feedback=final_feedback.model_dump(),
            source_count=100,
            revision=6,
        )

    @pytest.mark.asyncio
    async def test_finalize_without_previous_state_reduces_remaining_feedback(
        self,
    ):
        run_id = uuid4()

        remaining = [
            {
                "id": str(uuid4()),
                "feedback": "remaining feedback",
            }
        ]

        final_feedback = make_feedback(
            overall="Final feedback from remaining cases.",
        )

        buffer = make_buffer(
            size=1,
            pop_window=remaining,
        )

        state = make_state(
            current_state=None,
        )

        reducer = make_reducer(
            feedback=final_feedback,
        )

        service = make_service(
            buffer=buffer,
            state=state,
            reducer=reducer,
        )

        result = await service.finalize(
            run_id,
        )

        assert result["finalized"] is True
        assert result["source_count"] == 1
        assert result["revision"] == 1

        reducer.reduce.assert_awaited_once_with(
            current_feedback=None,
            feedback_items=remaining,
        )

    @pytest.mark.asyncio
    async def test_finalize_restores_remaining_items_when_reducer_fails(
        self,
    ):
        run_id = uuid4()

        remaining = [
            {
                "id": str(uuid4()),
                "feedback": "remaining feedback",
            }
        ]

        buffer = make_buffer(
            size=1,
            pop_window=remaining,
        )

        reducer = make_reducer()

        reducer.reduce.side_effect = RuntimeError("Summary reducer failed")

        service = make_service(
            buffer=buffer,
            reducer=reducer,
        )

        with pytest.raises(
            RuntimeError,
            match="Summary reducer failed",
        ):
            await service.finalize(
                run_id,
            )

        buffer.prepend.assert_awaited_once_with(
            run_id,
            remaining,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_clear_clears_buffer_and_state(
        self,
    ):
        run_id = uuid4()

        buffer = make_buffer()
        state = make_state()

        service = make_service(
            buffer=buffer,
            state=state,
        )

        await service.clear(
            run_id,
        )

        buffer.clear.assert_awaited_once_with(
            run_id,
        )

        state.clear.assert_awaited_once_with(
            run_id,
        )
