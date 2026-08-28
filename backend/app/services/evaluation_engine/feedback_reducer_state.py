import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class EvaluationFeedbackReducerState:
    """
    Stores the current rolling feedback-reducer state in Redis.

    Redis is temporary working storage only.
    PostgreSQL remains the source of truth.

    State contains:
        - current summary
        - source count
        - revision
    """

    KEY_PREFIX = "evaluation:feedback:"
    DEFAULT_TTL_SECONDS = 1800

    def __init__(
        self,
        redis: Redis,
        *,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @classmethod
    def build_key(
        cls,
        evaluation_run_id: UUID | str,
    ) -> str:
        return f"{cls.KEY_PREFIX}{evaluation_run_id}:state"

    async def get(
        self,
        evaluation_run_id: UUID | str,
    ) -> dict[str, Any] | None:
        """
        Return the current reducer state.

        Returns None when no state exists.
        """

        key = self.build_key(evaluation_run_id)

        cached = await self.redis.get(key)

        if cached is None:
            return None

        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")

        try:
            state = json.loads(cached)
        except (TypeError, json.JSONDecodeError):
            return None

        if not isinstance(state, dict):
            return None

        return state

    async def set(
        self,
        evaluation_run_id: UUID | str,
        *,
        feedback: dict[str, Any],
        source_count: int,
        revision: int,
    ) -> None:
        """
        Persist the latest rolling reducer state.

        The feedback object contains only qualitative fields:
            - overall
            - strengths
            - weaknesses
            - patterns
            - recommendations

        Raw evaluator feedback is intentionally not stored in the
        rolling state.
        """

        if not isinstance(feedback, dict):
            raise ValueError("feedback must be a dictionary.")

        if source_count < 0:
            raise ValueError("source_count must be non-negative.")

        if revision < 0:
            raise ValueError("revision must be non-negative.")

        payload = {
            "feedback": feedback,
            "source_count": source_count,
            "revision": revision,
        }

        key = self.build_key(evaluation_run_id)

        await self.redis.set(
            key,
            json.dumps(payload),
            ex=self.ttl_seconds,
        )

    async def clear(
        self,
        evaluation_run_id: UUID | str,
    ) -> None:
        """
        Remove the rolling reducer state.
        """

        await self.redis.delete(
            self.build_key(evaluation_run_id),
        )
