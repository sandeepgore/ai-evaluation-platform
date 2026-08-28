from unittest.mock import AsyncMock, MagicMock

from uuid import uuid4

import json

import pytest

from app.services.evaluation_engine.cache import EvaluationSummaryCache


@pytest.fixture
def redis():
    return MagicMock()


@pytest.fixture
def cache(redis):
    return EvaluationSummaryCache(redis=redis)


def test_build_key():
    run_id = uuid4()

    key = EvaluationSummaryCache.build_key(run_id)

    assert key == f"evaluation:summary:{run_id}"


@pytest.mark.asyncio
async def test_get_returns_none_on_cache_miss(cache, redis):
    redis.get = AsyncMock(return_value=None)

    run_id = uuid4()

    result = await cache.get(run_id)

    assert result is None
    redis.get.assert_awaited_once_with(f"evaluation:summary:{run_id}")


@pytest.mark.asyncio
async def test_get_returns_cached_summary(cache, redis):
    redis.get = AsyncMock(
        return_value=('{"overall_score": 0.75, "metrics": {"f1": 0.8}, "total_results": 5}')
    )

    run_id = uuid4()

    result = await cache.get(run_id)

    assert result == {
        "overall_score": 0.75,
        "metrics": {
            "f1": 0.8,
        },
        "total_results": 5,
    }

    redis.get.assert_awaited_once_with(f"evaluation:summary:{run_id}")


@pytest.mark.asyncio
async def test_get_handles_bytes_response(cache, redis):
    redis.get = AsyncMock(return_value=b'{"overall_score": 0.8}')

    run_id = uuid4()

    result = await cache.get(run_id)

    assert result == {
        "overall_score": 0.8,
    }


@pytest.mark.asyncio
async def test_set_stores_serialized_summary_with_ttl(cache, redis):
    redis.set = AsyncMock()

    run_id = uuid4()

    summary = {
        "overall_score": 0.75,
        "metrics": {
            "f1": 0.8,
        },
        "total_results": 5,
    }

    await cache.set(run_id, summary)

    redis.set.assert_awaited_once_with(
        f"evaluation:summary:{run_id}",
        ('{"overall_score": 0.75, "metrics": {"f1": 0.8}, "total_results": 5}'),
        ex=300,
    )


@pytest.mark.asyncio
async def test_set_uses_custom_ttl(redis):
    redis.set = AsyncMock()

    cache = EvaluationSummaryCache(
        redis=redis,
        ttl_seconds=60,
    )

    run_id = uuid4()

    summary = {
        "overall_score": 0.9,
    }

    await cache.set(run_id, summary)

    redis.set.assert_awaited_once_with(
        f"evaluation:summary:{run_id}",
        '{"overall_score": 0.9}',
        ex=60,
    )


@pytest.mark.asyncio
async def test_invalidate_deletes_cached_summary(cache, redis):
    redis.delete = AsyncMock(return_value=1)

    run_id = uuid4()

    await cache.invalidate(run_id)

    redis.delete.assert_awaited_once_with(f"evaluation:summary:{run_id}")


@pytest.mark.asyncio
async def test_invalidate_is_safe_when_key_does_not_exist(cache, redis):
    redis.delete = AsyncMock(return_value=0)

    run_id = uuid4()

    result = await cache.invalidate(run_id)

    assert result is None

    redis.delete.assert_awaited_once_with(f"evaluation:summary:{run_id}")


@pytest.mark.asyncio
async def test_cache_round_trip(cache, redis):
    run_id = uuid4()

    summary = {
        "model": {
            "name": "Qwen 2.5 3B Local",
            "provider": "ollama",
        },
        "overall_score": 0.64,
        "metrics": {
            "llm_judge": 0.64,
        },
        "total_results": 5,
        "completed_cases": 5,
        "failed_cases": 0,
    }

    stored_value = {}

    async def fake_set(key, value, ex):
        stored_value[key] = value

    async def fake_get(key):
        return stored_value.get(key)

    redis.set = AsyncMock(side_effect=fake_set)
    redis.get = AsyncMock(side_effect=fake_get)

    await cache.set(run_id, summary)

    result = await cache.get(run_id)

    assert result == summary


@pytest.mark.asyncio
async def test_set_serializes_uuid_values():
    redis = AsyncMock()

    cache = EvaluationSummaryCache(redis)

    run_id = uuid4()
    model_id = uuid4()

    summary = {
        "model": {
            "id": model_id,
            "name": "Qwen 2.5 3B Local",
        },
        "overall_score": 0.64,
    }

    await cache.set(run_id, summary)

    redis.set.assert_awaited_once()

    args, kwargs = redis.set.await_args

    cached_payload = json.loads(args[1])

    assert cached_payload["model"]["id"] == str(model_id)
    assert cached_payload["overall_score"] == 0.64
    assert kwargs["ex"] == EvaluationSummaryCache.DEFAULT_TTL_SECONDS
