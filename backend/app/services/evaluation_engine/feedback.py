from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation_result import EvaluationResult


class EvaluationRunFeedbackService:
    """
    Generates a deterministic run-level feedback summary from
    evaluator feedback stored on EvaluationResult records.

    This service intentionally does not call an LLM. It provides a
    predictable and inexpensive baseline that can later be extended
    with an optional LLM-generated executive summary.
    """

    @staticmethod
    def _normalize_feedback(
        feedback: str,
    ) -> str:
        return " ".join(feedback.strip().split())

    @classmethod
    def _extract_feedback_items(
        cls,
        results: list[EvaluationResult],
    ) -> list[str]:
        feedback_items: list[str] = []

        for result in results:
            if result.status != "completed":
                continue

            feedback = result.feedback

            if not isinstance(feedback, str):
                continue

            feedback = cls._normalize_feedback(feedback)

            if not feedback:
                continue

            # Evaluator feedback is currently stored as:
            #
            # metric: feedback
            #
            # Preserve the evaluator/metric prefix because it makes
            # the run-level summary more useful.
            feedback_items.append(feedback)

        return feedback_items

    @staticmethod
    def _build_summary(
        feedback_items: list[str],
        *,
        completed_cases: int,
        failed_cases: int,
    ) -> str | None:
        if not feedback_items:
            if failed_cases > 0:
                return (
                    f"Evaluation completed with {failed_cases} failed "
                    f"case(s). No evaluator feedback was available "
                    f"from the {completed_cases} completed case(s)."
                )

            return None

        counts = Counter(feedback_items)

        # Keep the summary intentionally small.
        # Repeated feedback is more useful than a long list of
        # individual case messages.
        ordered_feedback = sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )

        max_items = 5

        selected_feedback = ordered_feedback[:max_items]

        lines: list[str] = []

        if failed_cases > 0:
            lines.append(f"{failed_cases} case(s) failed during evaluation.")

        lines.append(
            f"Evaluator feedback was collected from {len(feedback_items)} completed case result(s)."
        )

        for feedback, count in selected_feedback:
            if count > 1:
                lines.append(f"- {feedback} (observed {count} times)")
            else:
                lines.append(f"- {feedback}")

        return "\n".join(lines)

    @classmethod
    async def generate(
        cls,
        db: AsyncSession,
        evaluation_run_id: Any,
    ) -> str | None:
        """
        Generate run-level feedback from completed evaluation results.
        """

        result = await db.execute(
            select(EvaluationResult).where(
                EvaluationResult.evaluation_run_id == evaluation_run_id,
                EvaluationResult.is_active.is_(True),
            )
        )

        results = list(result.scalars().all())

        completed_cases = sum(1 for item in results if item.status == "completed")

        failed_cases = sum(1 for item in results if item.status == "failed")

        feedback_items = cls._extract_feedback_items(results)

        return cls._build_summary(
            feedback_items,
            completed_cases=completed_cases,
            failed_cases=failed_cases,
        )
