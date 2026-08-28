import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class EvaluationFeedbackBuffer:
    """
    Redis-backed buffer for case-level evaluator feedback.

    Redis is temporary working storage only.
    PostgreSQL remains the source of truth.

    Each buffered item contains only:
        - evaluation result ID
        - feedback text
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
        return f"{cls.KEY_PREFIX}{evaluation_run_id}:pending"

    async def add(
        self,
        evaluation_run_id: UUID | str,
        result_id: UUID | str,
        feedback: str,
    ) -> None:
        """
        Append one feedback item to the pending Redis buffer.
        """

        if not isinstance(feedback, str):
            return

        feedback = " ".join(feedback.strip().split())

        if not feedback:
            return

        payload = {
            "id": str(result_id),
            "feedback": feedback,
        }

        key = self.build_key(evaluation_run_id)

        await self.redis.rpush(
            key,
            json.dumps(payload),
        )

        await self.redis.expire(
            key,
            self.ttl_seconds,
        )

    async def size(
        self,
        evaluation_run_id: UUID | str,
    ) -> int:
        """
        Return the number of pending feedback items.
        """

        key = self.build_key(evaluation_run_id)

        return await self.redis.llen(key)

    async def pop_window(
        self,
        evaluation_run_id: UUID | str,
        size: int,
    ) -> list[dict[str, Any]]:
        """
        Atomically remove up to `size` feedback items from the
        left side of the pending buffer.

        Redis LIST operations provide FIFO behavior.
        """

        if size <= 0:
            return []

        key = self.build_key(evaluation_run_id)

        items: list[dict[str, Any]] = []

        for _ in range(size):
            raw = await self.redis.lpop(key)

            if raw is None:
                break

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            try:
                payload = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                continue

            if not isinstance(payload, dict):
                continue

            result_id = payload.get("id")
            feedback = payload.get("feedback")

            if not isinstance(result_id, str):
                continue

            if not isinstance(feedback, str):
                continue

            items.append(
                {
                    "id": result_id,
                    "feedback": feedback,
                }
            )

        return items

    async def clear(
        self,
        evaluation_run_id: UUID | str,
    ) -> None:
        """
        Remove all pending feedback for an evaluation run.
        """

        key = self.build_key(evaluation_run_id)

        await self.redis.delete(key)

    async def prepend(
        self,
        evaluation_run_id: UUID | str,
        items: list[dict[str, Any]],
    ) -> None:
        """
        Put feedback items back at the front of the pending buffer.

        Items are restored in their original FIFO order.
        """

        if not items:
            return

        key = self.build_key(evaluation_run_id)

        values = [json.dumps(item) for item in reversed(items)]

        await self.redis.lpush(
            key,
            *values,
        )

        await self.redis.expire(
            key,
            self.ttl_seconds,
        )
