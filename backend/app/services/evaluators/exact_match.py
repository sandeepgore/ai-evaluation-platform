from typing import Any

from app.services.evaluators.base import EvaluationScore, Evaluator


class ExactMatchEvaluator(Evaluator):
    @property
    def name(self) -> str:
        return "exact_match"

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

        score = 1.0 if expected_output.strip() == actual_output.strip() else 0.0

        feedback = (
            "Output exactly matches the expected answer."
            if score == 1.0
            else "Output does not exactly match the expected answer."
        )

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=feedback,
        )
