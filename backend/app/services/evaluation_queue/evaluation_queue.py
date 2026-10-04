from uuid import UUID

from redis.asyncio import Redis

from app.config.settings import settings


class EvaluationQueue:
    """
    Redis Streams queue for evaluation runs.

    PostgreSQL remains the source of truth for evaluation run state.
    Redis only transports evaluation run IDs to workers.
    """

    def __init__(
        self,
        redis: Redis,
        stream: str,
        group: str,
    ):
        self.redis = redis
        self.stream = stream
        self.group = group

    async def initialize(self) -> None:
        """
        Create the consumer group if it does not already exist.
        """
        try:
            await self.redis.xgroup_create(
                name=self.stream,
                groupname=self.group,
                id="0",
                mkstream=True,
            )
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def enqueue(
        self,
        evaluation_run_id: UUID | str,
    ) -> str:
        """
        Add an evaluation run to the queue.

        Returns:
            Redis stream message ID.
        """
        message_id = await self.redis.xadd(
            self.stream,
            {
                "evaluation_run_id": str(evaluation_run_id),
            },
        )

        return str(message_id)

    async def acknowledge(
        self,
        message_id: str,
    ) -> None:
        """
        Acknowledge successful processing of a queue message.
        """
        await self.redis.xack(
            self.stream,
            self.group,
            message_id,
        )

    async def consume(
        self,
        consumer: str,
        block_ms: int = 5_000,
    ) -> tuple[str, str] | None:
        """
        Consume one new evaluation job from the Redis stream.

        Only messages that have never been delivered to a consumer
        are returned.

        Returns:
            (message_id, evaluation_run_id)
            or None when no message is available.
        """
        messages = await self.redis.xreadgroup(
            groupname=self.group,
            consumername=consumer,
            streams={self.stream: ">"},
            count=1,
            block=block_ms,
        )

        if not messages:
            return None

        _stream_name, entries = messages[0]
        message_id, data = entries[0]

        evaluation_run_id = data.get("evaluation_run_id")

        if evaluation_run_id is None:
            raise ValueError("Evaluation queue message is missing evaluation_run_id.")

        return str(message_id), str(evaluation_run_id)

    async def refresh_claim(
        self,
        consumer: str,
        message_id: str,
    ) -> bool:
        """
        Refresh the Redis pending-message claim for a live evaluation.

        The message remains owned by the same consumer while its idle
        time is refreshed. This prevents a legitimately long-running
        evaluation from being considered stale by reclaim_stale().

        Returns:
            True if the message is still pending and the claim was
            refreshed, otherwise False.
        """
        claimed_messages = await self.redis.xclaim(
            name=self.stream,
            groupname=self.group,
            consumername=consumer,
            min_idle_time=0,
            message_ids=[message_id],
        )

        return bool(claimed_messages)

    async def reclaim_stale(
        self,
        consumer: str,
    ) -> tuple[str, str] | None:
        """
        Reclaim one stale pending evaluation job.

        A message becomes eligible for recovery when it has been
        pending for longer than the configured queue claim timeout.

        Returns:
            (message_id, evaluation_run_id)
            or None when no stale message is available.

        Notes:
            - Only pending messages are considered.
            - The message is transferred to the supplied consumer.
            - Redis does not determine whether the evaluation run
              should execute; PostgreSQL remains the source of truth.
        """
        min_idle_time_ms = settings.evaluation_queue_claim_timeout_seconds * 1_000

        result = await self.redis.xautoclaim(
            name=self.stream,
            groupname=self.group,
            consumername=consumer,
            min_idle_time=min_idle_time_ms,
            start_id="0-0",
            count=1,
        )

        if not result:
            return None

        _next_start_id = result[0]
        entries = result[1]

        if not entries:
            return None

        message_id, data = entries[0]

        evaluation_run_id = data.get("evaluation_run_id")

        if evaluation_run_id is None:
            raise ValueError("Evaluation queue message is missing evaluation_run_id.")

        return str(message_id), str(evaluation_run_id)
