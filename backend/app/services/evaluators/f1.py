import re
import unicodedata
from collections import Counter
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class F1Evaluator(Evaluator):
    """
    Deterministic token-level F1 evaluator.

    Compares the expected/reference output with the actual model
    output using token overlap.

    The evaluator calculates:

        precision = overlapping_tokens / actual_tokens
        recall = overlapping_tokens / expected_tokens

        F1 = 2 * precision * recall / (precision + recall)

    Characteristics:
        - Requires expected/reference output.
        - Requires actual model output.
        - Does not require evaluation context.
        - Does not use an LLM.
        - Does not use embeddings.
        - Matching is case-insensitive.
        - Unicode text is normalized using NFKC.
        - Punctuation is ignored during tokenization.
        - Repeated tokens are handled using token frequencies.

    This is a lexical F1 metric. It measures token-level overlap,
    not semantic similarity.
    """

    @property
    def name(self) -> str:
        """Return the unique evaluator name."""
        return "f1"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """Return static metadata describing the F1 evaluator."""
        return EvaluatorMetadata(
            category="correctness",
            description=(
                "Measures token-level F1 overlap between the model output "
                "and the reference answer using precision and recall."
            ),
            required_inputs=(
                "actual_output",
                "expected_output",
            ),
            requires_reference=True,
            requires_context=False,
            requires_llm=False,
            applicable_to=("text", "rag"),
            tags=(
                "deterministic",
                "reference-based",
                "token-overlap",
                "f1",
            ),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize Unicode and casing before tokenization.
        """
        return unicodedata.normalize("NFKC", text).lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """
        Tokenize text while ignoring punctuation.

        Tokenization is intentionally deterministic so the same
        inputs always produce the same metric result.
        """
        normalized = cls._normalize_text(text)

        return re.findall(
            r"\b\w+\b",
            normalized,
            flags=re.UNICODE,
        )

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Calculate token-level F1 between expected and actual output.

        Args:
            expected_output:
                Reference/ground-truth answer.

            actual_output:
                Model-generated answer.

            context:
                Optional evaluation context. Not required by this
                evaluator.

        Returns:
            EvaluationScore containing:
                - score: token-level F1 score in the range [0, 1]
                - feedback: human-readable metric feedback
                - metadata: precision, recall, overlap and token counts
        """

        # --------------------------------------------------------------
        # Validate inputs
        # --------------------------------------------------------------

        if expected_output is None or actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is missing.",
            )

        # --------------------------------------------------------------
        # Tokenize both outputs
        # --------------------------------------------------------------

        expected_tokens = self._tokenize(expected_output)
        actual_tokens = self._tokenize(actual_output)

        if not expected_tokens or not actual_tokens:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is empty.",
            )

        # --------------------------------------------------------------
        # Count token frequencies
        #
        # Counter intersection preserves the minimum frequency for
        # tokens appearing in both outputs.
        # --------------------------------------------------------------

        expected_counts = Counter(expected_tokens)
        actual_counts = Counter(actual_tokens)

        common_tokens = expected_counts & actual_counts

        overlap = sum(common_tokens.values())

        # --------------------------------------------------------------
        # No overlap
        # --------------------------------------------------------------

        if overlap == 0:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="No token overlap between expected and actual output.",
                metadata={
                    "precision": 0.0,
                    "recall": 0.0,
                    "overlap": 0,
                    "expected_tokens": len(expected_tokens),
                    "actual_tokens": len(actual_tokens),
                },
            )

        # --------------------------------------------------------------
        # Precision
        # --------------------------------------------------------------

        precision = overlap / len(actual_tokens)

        # --------------------------------------------------------------
        # Recall
        # --------------------------------------------------------------

        recall = overlap / len(expected_tokens)

        # --------------------------------------------------------------
        # F1
        # --------------------------------------------------------------

        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

        # --------------------------------------------------------------
        # Return standardized evaluation result
        # --------------------------------------------------------------

        return EvaluationScore(
            metric=self.name,
            score=f1,
            feedback=f"Token-level F1 score: {f1:.4f}.",
            metadata={
                "precision": precision,
                "recall": recall,
                "overlap": overlap,
                "expected_tokens": len(expected_tokens),
                "actual_tokens": len(actual_tokens),
            },
        )
