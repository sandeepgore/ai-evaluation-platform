from typing import Any

from app.services.evaluators.base import EvaluationScore, Evaluator


class ContainsEvaluator(Evaluator):
    """
    Checks whether the expected output is contained within
    the actual model output.

    Example:

        expected = "Paris"
        actual = "The capital of France is Paris."

        score = 1.0
    """

    @property
    def name(self) -> str:
        return "contains"

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:

        if expected_output is None or actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is missing.",
            )

        expected = expected_output.strip().lower()
        actual = actual_output.strip().lower()

        if not expected:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output is empty.",
            )

        score = 1.0 if expected in actual else 0.0

        feedback = (
            "Expected output is contained in the actual output."
            if score == 1.0
            else "Expected output is not contained in the actual output."
        )

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=feedback,
        )

