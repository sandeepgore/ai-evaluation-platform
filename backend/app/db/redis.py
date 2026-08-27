from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.config.settings import settings


async def get_redis() -> AsyncIterator[Redis]:
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        yield redis
    finally:
        await redis.aclose()
