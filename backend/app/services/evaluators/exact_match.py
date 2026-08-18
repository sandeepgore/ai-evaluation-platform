import unicodedata
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class ExactMatchEvaluator(Evaluator):
    """
    Deterministic exact-match evaluator.

    Compares the expected/reference output with the actual model output
    after applying the evaluator's normalization rules.

    Normalization rules:
        1. Unicode is normalized using NFKC.
        2. Leading and trailing whitespace is removed.
        3. Case is preserved.
        4. Punctuation is preserved.
        5. Internal whitespace is preserved.

    Examples:

        expected = "Paris"
        actual   = "Paris"

        score = 1.0

        expected = "Paris"
        actual   = " paris "

        score = 0.0

    This evaluator is intentionally strict after normalization.
    It does not perform semantic matching, fuzzy matching, token
    normalization, or case-insensitive comparison.
    """

    @property
    def name(self) -> str:
        """Return the unique evaluator name."""
        return "exact_match"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing the exact-match evaluator.
        """
        return EvaluatorMetadata(
            category="correctness",
            description=(
                "Checks whether the model output exactly matches "
                "the reference answer after applying normalization."
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
                "exact-match",
                "normalizable",
            ),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Apply the exact-match normalization rules.

        Normalization intentionally:
            - applies Unicode NFKC normalization
            - strips leading/trailing whitespace
            - preserves case
            - preserves punctuation
            - preserves internal whitespace
        """
        return unicodedata.normalize(
            "NFKC",
            text,
        ).strip()

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Evaluate whether the normalized actual output exactly matches
        the normalized expected output.
        """

        if expected_output is None or actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is missing.",
            )

        expected = self._normalize_text(expected_output)
        actual = self._normalize_text(actual_output)

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
            metadata={
                "normalization": {
                    "unicode": "NFKC",
                    "strip_surrounding_whitespace": True,
                    "case_sensitive": True,
                    "preserve_punctuation": True,
                    "preserve_internal_whitespace": True,
                },
            },
        )
