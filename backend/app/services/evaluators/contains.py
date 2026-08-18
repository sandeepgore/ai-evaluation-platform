from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class ContainsEvaluator(Evaluator):
    """
    Deterministic substring-based evaluator.

    Checks whether the expected/reference output is contained within
    the actual model output.

    Example:
        expected = "Paris"
        actual = "The capital of France is Paris."

        score = 1.0

    Characteristics:
        - Requires an expected/reference output.
        - Does not require evaluation context.
        - Does not use an LLM.
        - Case-insensitive.
        - Ignores leading/trailing whitespace.
        - Returns a deterministic score of 0.0 or 1.0.

    This evaluator intentionally performs lexical substring matching.
    It does not perform semantic similarity or fuzzy matching.
    """

    @property
    def name(self) -> str:
        """Return the unique evaluator name."""
        return "contains"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing this evaluator.
        """
        return EvaluatorMetadata(
            category="correctness",
            description=(
                "Checks whether the reference answer is contained "
                "within the model output using case-insensitive "
                "substring matching."
            ),
            required_inputs=(
                "actual_output",
                "expected_output",
            ),
            requires_reference=True,
            requires_context=False,
            requires_llm=False,
            applicable_to=("text",),
            tags=(
                "deterministic",
                "reference-based",
                "substring",
                "case-insensitive",
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
        Evaluate whether the expected output is contained
        within the actual model output.

        Args:
            expected_output:
                Reference/ground-truth answer that should appear
                in the model output.

            actual_output:
                Model-generated answer.

            context:
                Optional evaluation context. Not required by this
                evaluator.

        Returns:
            EvaluationScore containing a deterministic 0.0 or 1.0 score.
        """

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
                metadata={
                    "normalization": {
                        "lowercase": True,
                        "strip_whitespace": True,
                    },
                },
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
            metadata={
                "normalization": {
                    "lowercase": True,
                    "strip_whitespace": True,
                },
            },
        )
