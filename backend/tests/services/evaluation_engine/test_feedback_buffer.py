import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.evaluation_engine.feedback_buffer import (
    EvaluationFeedbackBuffer,
)


@pytest.fixture
def redis():
    return AsyncMock()


@pytest.fixture
def buffer(redis):
    return EvaluationFeedbackBuffer(redis=redis)


class TestEvaluationFeedbackBuffer:
    def test_build_key(self):
        run_id = uuid4()

        key = EvaluationFeedbackBuffer.build_key(run_id)

        assert key == f"evaluation:feedback:{run_id}:pending"

    def test_build_key_accepts_string(self):
        run_id = str(uuid4())

        key = EvaluationFeedbackBuffer.build_key(run_id)

        assert key == f"evaluation:feedback:{run_id}:pending"

    @pytest.mark.asyncio
    async def test_add_stores_id_and_feedback(self, buffer, redis):
        run_id = uuid4()
        result_id = uuid4()

        redis.rpush = AsyncMock()
        redis.expire = AsyncMock()

        await buffer.add(
            run_id,
            result_id,
            "  feedback   with   extra whitespace  ",
        )

        redis.rpush.assert_awaited_once()

        key, raw_payload = redis.rpush.await_args.args

        assert key == EvaluationFeedbackBuffer.build_key(run_id)

        payload = json.loads(raw_payload)

        assert payload == {
            "id": str(result_id),
            "feedback": "feedback with extra whitespace",
        }

        redis.expire.assert_awaited_once_with(
            key,
            EvaluationFeedbackBuffer.DEFAULT_TTL_SECONDS,
        )

    @pytest.mark.asyncio
    async def test_add_ignores_non_string_feedback(self, buffer, redis):
        redis.rpush = AsyncMock()
        redis.expire = AsyncMock()

        await buffer.add(
            uuid4(),
            uuid4(),
            None,
        )

        redis.rpush.assert_not_awaited()
        redis.expire.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_ignores_empty_feedback(self, buffer, redis):
        redis.rpush = AsyncMock()
        redis.expire = AsyncMock()

        await buffer.add(
            uuid4(),
            uuid4(),
            "   ",
        )

        redis.rpush.assert_not_awaited()
        redis.expire.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_size_returns_pending_count(self, buffer, redis):
        run_id = uuid4()

        redis.llen = AsyncMock(return_value=17)

        result = await buffer.size(run_id)

        assert result == 17

        redis.llen.assert_awaited_once_with(EvaluationFeedbackBuffer.build_key(run_id))

    @pytest.mark.asyncio
    async def test_pop_window_returns_fifo_items(self, buffer, redis):
        run_id = uuid4()

        first = {
            "id": str(uuid4()),
            "feedback": "first feedback",
        }

        second = {
            "id": str(uuid4()),
            "feedback": "second feedback",
        }

        third = {
            "id": str(uuid4()),
            "feedback": "third feedback",
        }

        redis.lpop = AsyncMock(
            side_effect=[
                json.dumps(first),
                json.dumps(second),
                json.dumps(third),
                None,
            ]
        )

        result = await buffer.pop_window(
            run_id,
            3,
        )

        assert result == [
            first,
            second,
            third,
        ]

        assert redis.lpop.await_count == 3

        expected_key = EvaluationFeedbackBuffer.build_key(run_id)

        for call in redis.lpop.await_args_list:
            assert call.args == (expected_key,)

    @pytest.mark.asyncio
    async def test_pop_window_stops_when_buffer_is_empty(self, buffer, redis):
        run_id = uuid4()

        redis.lpop = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "id": str(uuid4()),
                        "feedback": "feedback",
                    }
                ),
                None,
            ]
        )

        result = await buffer.pop_window(
            run_id,
            10,
        )

        assert len(result) == 1
        assert redis.lpop.await_count == 2

    @pytest.mark.asyncio
    async def test_pop_window_with_non_positive_size_returns_empty(
        self,
        buffer,
        redis,
    ):
        result = await buffer.pop_window(
            uuid4(),
            0,
        )

        assert result == []
        redis.lpop.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_pop_window_ignores_invalid_json(self, buffer, redis):
        run_id = uuid4()

        valid = {
            "id": str(uuid4()),
            "feedback": "valid feedback",
        }

        redis.lpop = AsyncMock(
            side_effect=[
                "not-json",
                json.dumps(valid),
                None,
            ]
        )

        result = await buffer.pop_window(
            run_id,
            3,
        )

        assert result == [valid]

    @pytest.mark.asyncio
    async def test_pop_window_ignores_invalid_payload(self, buffer, redis):
        run_id = uuid4()

        redis.lpop = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "id": "missing-feedback",
                    }
                ),
                json.dumps(
                    {
                        "feedback": "missing-id",
                    }
                ),
                json.dumps(
                    {
                        "id": "valid-id",
                        "feedback": "valid feedback",
                    }
                ),
            ]
        )

        result = await buffer.pop_window(
            run_id,
            3,
        )

        assert result == [
            {
                "id": "valid-id",
                "feedback": "valid feedback",
            }
        ]

    @pytest.mark.asyncio
    async def test_clear_deletes_pending_buffer(self, buffer, redis):
        run_id = uuid4()

        redis.delete = AsyncMock()

        await buffer.clear(run_id)

        redis.delete.assert_awaited_once_with(EvaluationFeedbackBuffer.build_key(run_id))
