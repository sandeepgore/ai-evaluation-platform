import asyncio
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.config.settings import settings
from app.services.evaluation_queue.evaluation_queue import EvaluationQueue


@pytest.mark.asyncio
async def test_evaluation_queue_refresh_claim_keeps_live_message_owned():
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    stream = f"{settings.evaluation_queue_stream}:refresh-test"
    group = f"{settings.evaluation_queue_group}:refresh-test"

    queue = EvaluationQueue(
        redis=redis,
        stream=stream,
        group=group,
    )

    consumer_one = "refresh-test-worker-1"
    consumer_two = "refresh-test-worker-2"

    try:
        await queue.initialize()

        evaluation_run_id = uuid4()

        message_id = await queue.enqueue(
            evaluation_run_id,
        )

        consumed = await queue.consume(
            consumer=consumer_one,
            block_ms=1_000,
        )

        assert consumed == (
            message_id,
            str(evaluation_run_id),
        )

        refreshed = await queue.refresh_claim(
            consumer=consumer_one,
            message_id=message_id,
        )

        assert refreshed is True

        reclaimed = await queue.reclaim_stale(
            consumer=consumer_two,
        )

        assert reclaimed is None

        pending = await redis.xpending(
            stream,
            group,
        )

        assert pending["pending"] == 1

    finally:
        await redis.delete(stream)
        await redis.aclose()
