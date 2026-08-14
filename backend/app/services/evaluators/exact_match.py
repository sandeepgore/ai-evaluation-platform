from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class ExactMatchEvaluator(Evaluator):
    """
    Exact-match evaluator.

    Compares the expected output with the actual model output after
    trimming leading and trailing whitespace.

    Score:
        1.0 -> outputs match exactly after stripping whitespace
        0.0 -> outputs do not match

    This evaluator:
        - requires an expected/reference output
        - does not require evaluation context
        - does not use an LLM
        - is deterministic
    """

    @property
    def name(self) -> str:
        """Return the unique evaluator name."""
        return "exact_match"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing this evaluator.
        """
        return EvaluatorMetadata(
            category="correctness",
            description=(
                "Checks whether the model output exactly matches "
                "the reference answer after trimming surrounding whitespace."
            ),
            requires_reference=True,
            requires_context=False,
            requires_llm=False,
            applicable_to=("text",),
            tags=(
                "deterministic",
                "reference-based",
                "exact-match",
            ),
        )

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Evaluate whether the actual output exactly matches
        the expected output.
        """

        if expected_output is None or actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is missing.",
            )

        expected = expected_output.strip()
        actual = actual_output.strip()

        score = 1.0 if expected == actual else 0.0

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
