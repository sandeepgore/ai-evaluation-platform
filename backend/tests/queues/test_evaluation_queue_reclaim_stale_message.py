import asyncio
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.config.settings import settings
from app.services.evaluation_queue.evaluation_queue import EvaluationQueue


@pytest.mark.asyncio
async def test_evaluation_queue_reclaim_stale_message():
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    stream = f"{settings.evaluation_queue_stream}:stale-test"
    group = f"{settings.evaluation_queue_group}:stale-test"

    queue = EvaluationQueue(
        redis=redis,
        stream=stream,
        group=group,
    )

    consumer_one = "stale-test-worker-1"
    consumer_two = "stale-test-worker-2"

    original_timeout = settings.evaluation_queue_claim_timeout_seconds

    try:
        settings.evaluation_queue_claim_timeout_seconds = 1

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

        await asyncio.sleep(1.2)

        reclaimed = await queue.reclaim_stale(
            consumer=consumer_two,
        )

        assert reclaimed == (
            message_id,
            str(evaluation_run_id),
        )

        pending = await redis.xpending(
            stream,
            group,
        )

        assert pending["pending"] == 1

    finally:
        settings.evaluation_queue_claim_timeout_seconds = original_timeout

        await redis.delete(stream)
        await redis.aclose()
