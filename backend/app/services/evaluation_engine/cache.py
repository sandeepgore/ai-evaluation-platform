import json
from uuid import UUID

from redis.asyncio import Redis


class EvaluationSummaryCache:
    """
    Redis cache for evaluation run summaries.

    Redis is a cache only. PostgreSQL remains the source of truth.
    """

    KEY_PREFIX = "evaluation:summary:"
    DEFAULT_TTL_SECONDS = 300

    def __init__(
        self,
        redis: Redis,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @classmethod
    def build_key(cls, evaluation_run_id: UUID | str) -> str:
        return f"{cls.KEY_PREFIX}{evaluation_run_id}"

    async def get(
        self,
        evaluation_run_id: UUID | str,
    ) -> dict | None:
        key = self.build_key(evaluation_run_id)

        cached = await self.redis.get(key)

        if cached is None:
            return None

        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")

        return json.loads(cached)

    async def set(
        self,
        evaluation_run_id: UUID | str,
        summary: dict,
    ) -> None:
        key = self.build_key(evaluation_run_id)

        await self.redis.set(
            key,
            json.dumps(summary, default=str),
            ex=self.ttl_seconds,
        )

    async def invalidate(
        self,
        evaluation_run_id: UUID | str,
    ) -> None:
        key = self.build_key(evaluation_run_id)

        await self.redis.delete(key)
