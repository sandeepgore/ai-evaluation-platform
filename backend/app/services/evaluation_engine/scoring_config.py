import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun


class ScoringConfigurationService:
    """
    Resolves and caches evaluation-run scoring configuration.

    PostgreSQL is the source of truth.

    Redis is used as a performance optimization so the scoring
    configuration does not need to be repeatedly resolved from the
    database during large evaluation runs.
    """

    CACHE_PREFIX = "evaluation:run:scoring-config"
    DEFAULT_TTL_SECONDS = 3600

    def __init__(
        self,
        redis: Redis | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @classmethod
    def _cache_key(
        cls,
        evaluation_run_id: UUID,
    ) -> str:
        return f"{cls.CACHE_PREFIX}:{evaluation_run_id}"

    @staticmethod
    def _extract_configuration(
        run: EvaluationRun,
    ) -> dict[str, Any]:
        configuration = run.configuration or {}

        if not isinstance(configuration, dict):
            return {}

        scoring_configuration = configuration.get(
            "scoring",
            {},
        )

        if not isinstance(scoring_configuration, dict):
            return {}

        return scoring_configuration.copy()

    async def get(
        self,
        db: AsyncSession,
        evaluation_run_id: UUID,
    ) -> dict[str, Any]:
        """
        Resolve scoring configuration.

        Resolution order:

            Redis
              ↓ cache hit
            return configuration

            Redis
              ↓ cache miss/failure
            PostgreSQL
              ↓
            populate Redis
              ↓
            return configuration
        """

        cache_key = self._cache_key(evaluation_run_id)

        # ----------------------------------------------------------
        # 1. Redis cache
        # ----------------------------------------------------------

        if self.redis is not None:
            try:
                cached = await self.redis.get(cache_key)

                if cached is not None:
                    if isinstance(cached, bytes):
                        cached = cached.decode("utf-8")

                    configuration = json.loads(cached)

                    if isinstance(configuration, dict):
                        return configuration

            except Exception:
                # Redis is an optimization only.
                # A Redis failure must never break evaluation.
                pass

        # ----------------------------------------------------------
        # 2. PostgreSQL source of truth
        # ----------------------------------------------------------

        result = await db.execute(
            select(EvaluationRun).where(
                EvaluationRun.id == evaluation_run_id,
                EvaluationRun.is_active.is_(True),
            )
        )

        run = result.scalar_one_or_none()

        if run is None:
            raise ValueError("Evaluation run not found.")

        scoring_configuration = self._extract_configuration(run)

        # ----------------------------------------------------------
        # 3. Populate Redis
        # ----------------------------------------------------------

        if self.redis is not None:
            try:
                await self.redis.set(
                    cache_key,
                    json.dumps(scoring_configuration),
                    ex=self.ttl_seconds,
                )
            except Exception:
                # Cache population failure must not affect evaluation.
                pass

        return scoring_configuration

    async def invalidate(
        self,
        evaluation_run_id: UUID,
    ) -> None:
        """
        Remove cached scoring configuration for an evaluation run.
        """

        if self.redis is None:
            return

        cache_key = self._cache_key(evaluation_run_id)

        try:
            await self.redis.delete(cache_key)
        except Exception:
            # Cache invalidation failure must not break the application.
            pass
