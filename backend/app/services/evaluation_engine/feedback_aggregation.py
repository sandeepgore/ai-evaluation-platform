from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from app.schemas.evaluation.summary import EvaluationRunFeedbackResponse
from app.services.evaluation_engine.feedback_buffer import (
    EvaluationFeedbackBuffer,
)
from app.services.evaluation_engine.feedback_reducer import (
    EvaluationFeedbackReducer,
)
from app.services.evaluation_engine.feedback_reducer_state import (
    EvaluationFeedbackReducerState,
)


class EvaluationFeedbackAggregationService:
    """
    Coordinates the rolling feedback reduction pipeline.

    Redis contains only:
        - pending case-level feedback
        - current rolling reducer state

    The reducer follows a sliding-window strategy:

        First reduction:
            20 new feedback items

        Subsequent reductions:
            1 current rolling summary
            + 19 new feedback items

    PostgreSQL remains the source of truth for case-level feedback.
    """

    DEFAULT_WINDOW_SIZE = 20
    # REDUCER_INPUT_SIZE = DEFAULT_WINDOW_SIZE - 1

    LOCK_KEY_PREFIX = "evaluation:feedback:"
    LOCK_TTL_SECONDS = 120

    def __init__(
        self,
        redis: Redis,
        reducer: EvaluationFeedbackReducer,
        *,
        window_size: int = DEFAULT_WINDOW_SIZE,
        buffer: EvaluationFeedbackBuffer | None = None,
        state: EvaluationFeedbackReducerState | None = None,
    ) -> None:
        if window_size < 2:
            raise ValueError("window_size must be at least 2.")

        self.redis = redis
        self.reducer = reducer
        self.window_size = window_size
        self.reducer_input_size = window_size - 1

        self.buffer = buffer or EvaluationFeedbackBuffer(
            redis,
        )

        self.state = state or EvaluationFeedbackReducerState(
            redis,
        )

    @classmethod
    def build_lock_key(
        cls,
        evaluation_run_id: UUID | str,
    ) -> str:
        return f"{cls.LOCK_KEY_PREFIX}{evaluation_run_id}:reduce-lock"

    async def accept(
        self,
        evaluation_run_id: UUID | str,
        result_id: UUID | str,
        feedback: str | None,
    ) -> dict[str, Any]:
        """
        Add one case-level feedback item and reduce when the
        rolling window threshold is reached.
        """

        if isinstance(feedback, str) and feedback.strip():
            await self.buffer.add(
                evaluation_run_id,
                result_id,
                feedback,
            )

        return await self.reduce_if_ready(
            evaluation_run_id,
        )

    async def reduce_if_ready(
        self,
        evaluation_run_id: UUID | str,
    ) -> dict[str, Any]:
        """
        Reduce one rolling window when the threshold has been reached.

        Returns information about whether a reduction occurred.
        """

        lock_token = await self._acquire_lock(
            evaluation_run_id,
        )

        if lock_token is None:
            return {
                "reduced": False,
                "reason": "reduction_in_progress",
            }

        try:
            current_state = await self.state.get(
                evaluation_run_id,
            )

            current_feedback = self._state_feedback(
                current_state,
            )

            pending_size = await self.buffer.size(
                evaluation_run_id,
            )

            threshold = self.window_size if current_feedback is None else self.reducer_input_size

            if pending_size < threshold:
                return {
                    "reduced": False,
                    "reason": "threshold_not_reached",
                    "pending": pending_size,
                    "threshold": threshold,
                }

            feedback_items = await self.buffer.pop_window(
                evaluation_run_id,
                threshold,
            )

            if len(feedback_items) < threshold:
                if feedback_items:
                    await self.buffer.prepend(
                        evaluation_run_id,
                        feedback_items,
                    )

                return {
                    "reduced": False,
                    "reason": "insufficient_items",
                }

            previous_source_count = self._state_source_count(
                current_state,
            )

            try:
                reduced_feedback = await self.reducer.reduce(
                    current_feedback=current_feedback,
                    feedback_items=feedback_items,
                )

            except Exception:
                await self.buffer.prepend(
                    evaluation_run_id,
                    feedback_items,
                )
                raise

            source_count = previous_source_count + len(feedback_items)

            revision = (
                self._state_revision(
                    current_state,
                )
                + 1
            )

            await self.state.set(
                evaluation_run_id,
                feedback=reduced_feedback.model_dump(),
                source_count=source_count,
                revision=revision,
            )

            return {
                "reduced": True,
                "source_count": source_count,
                "revision": revision,
                "pending": max(
                    pending_size - len(feedback_items),
                    0,
                ),
                "feedback": reduced_feedback.model_dump(),
            }

        finally:
            await self._release_lock(
                evaluation_run_id,
                lock_token,
            )

    async def finalize(
        self,
        evaluation_run_id: UUID | str,
    ) -> dict[str, Any]:
        """
        Finalize the rolling feedback state at the end of a run.

        Any remaining feedback items are merged into the current
        rolling feedback, even when fewer than the normal threshold
        remain.
        """

        lock_token = await self._acquire_lock(
            evaluation_run_id,
        )

        if lock_token is None:
            return {
                "finalized": False,
                "reason": "reduction_in_progress",
            }

        try:
            current_state = await self.state.get(
                evaluation_run_id,
            )

            current_feedback = self._state_feedback(
                current_state,
            )

            remaining = await self.buffer.pop_window(
                evaluation_run_id,
                await self.buffer.size(
                    evaluation_run_id,
                ),
            )

            if not remaining:
                return {
                    "finalized": True,
                    "feedback": (
                        current_feedback.model_dump() if current_feedback is not None else None
                    ),
                    "source_count": self._state_source_count(
                        current_state,
                    ),
                    "revision": self._state_revision(
                        current_state,
                    ),
                }

            previous_source_count = self._state_source_count(
                current_state,
            )

            try:
                final_feedback = await self.reducer.reduce(
                    current_feedback=current_feedback,
                    feedback_items=remaining,
                )

            except Exception:
                await self.buffer.prepend(
                    evaluation_run_id,
                    remaining,
                )
                raise

            source_count = previous_source_count + len(remaining)

            revision = (
                self._state_revision(
                    current_state,
                )
                + 1
            )

            await self.state.set(
                evaluation_run_id,
                feedback=final_feedback.model_dump(),
                source_count=source_count,
                revision=revision,
            )

            return {
                "finalized": True,
                "feedback": final_feedback.model_dump(),
                "source_count": source_count,
                "revision": revision,
            }

        finally:
            await self._release_lock(
                evaluation_run_id,
                lock_token,
            )

    async def clear(
        self,
        evaluation_run_id: UUID | str,
    ) -> None:
        """
        Clear transient Redis feedback state after final persistence.
        """

        await self.buffer.clear(
            evaluation_run_id,
        )

        await self.state.clear(
            evaluation_run_id,
        )

    @staticmethod
    def _state_feedback(
        state: dict[str, Any] | None,
    ) -> EvaluationRunFeedbackResponse | None:
        if not state:
            return None

        feedback = state.get(
            "feedback",
        )

        if not isinstance(feedback, dict):
            return None

        try:
            return EvaluationRunFeedbackResponse(
                overall=str(feedback.get("overall", "")),
                strengths=(
                    feedback.get("strengths", [])
                    if isinstance(
                        feedback.get("strengths", []),
                        list,
                    )
                    else []
                ),
                weaknesses=(
                    feedback.get("weaknesses", [])
                    if isinstance(
                        feedback.get("weaknesses", []),
                        list,
                    )
                    else []
                ),
                patterns=(
                    feedback.get("patterns", [])
                    if isinstance(
                        feedback.get("patterns", []),
                        list,
                    )
                    else []
                ),
                recommendations=(
                    feedback.get("recommendations", [])
                    if isinstance(
                        feedback.get("recommendations", []),
                        list,
                    )
                    else []
                ),
                evaluator_feedback=[],
            )

        except Exception:
            return None

    @staticmethod
    def _state_source_count(
        state: dict[str, Any] | None,
    ) -> int:
        if not state:
            return 0

        value = state.get(
            "source_count",
            0,
        )

        if not isinstance(value, int):
            return 0

        return max(
            value,
            0,
        )

    @staticmethod
    def _state_revision(
        state: dict[str, Any] | None,
    ) -> int:
        if not state:
            return 0

        value = state.get(
            "revision",
            0,
        )

        if not isinstance(value, int):
            return 0

        return max(
            value,
            0,
        )

    async def _acquire_lock(
        self,
        evaluation_run_id: UUID | str,
    ) -> str | None:
        """
        Acquire a short-lived distributed reduction lock.
        """

        import uuid

        token = str(uuid.uuid4())

        acquired = await self.redis.set(
            self.build_lock_key(
                evaluation_run_id,
            ),
            token,
            nx=True,
            ex=self.LOCK_TTL_SECONDS,
        )

        if not acquired:
            return None

        return token

    async def _release_lock(
        self,
        evaluation_run_id: UUID | str,
        token: str | None,
    ) -> None:
        """
        Release the lock only when it still belongs to this worker.
        """

        if token is None:
            return

        key = self.build_lock_key(
            evaluation_run_id,
        )

        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        end
        return 0
        """

        try:
            await self.redis.eval(
                script,
                1,
                key,
                token,
            )
        except Exception:
            pass
