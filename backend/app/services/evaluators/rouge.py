import re
import unicodedata
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class ROUGELvaluator(Evaluator):
    """
    Deterministic ROUGE-L evaluator based on Longest Common
    Subsequence (LCS).

    ROUGE-L measures the similarity between generated output
    and a reference answer based on the longest common
    subsequence of tokens.

    Characteristics:
        - Requires expected/reference output.
        - Does not require evaluation context.
        - Does not use an LLM.
        - Does not use embeddings.
        - Uses case-insensitive token matching.
        - Normalizes Unicode using NFKC.
        - Ignores punctuation during tokenization.
        - Uses deterministic LCS-based scoring.
    """

    @property
    def name(self) -> str:
        """Return the unique evaluator name."""
        return "rouge_l"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing the ROUGE-L evaluator.
        """
        return EvaluatorMetadata(
            category="similarity",
            description=(
                "Measures longest common subsequence overlap between "
                "the model output and the reference answer using "
                "deterministic ROUGE-L scoring."
            ),
            requires_reference=True,
            requires_context=False,
            requires_llm=False,
            applicable_to=("text",),
            tags=(
                "deterministic",
                "reference-based",
                "lcs",
                "rouge",
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
        """
        normalized = cls._normalize_text(text)

        return re.findall(
            r"\b\w+\b",
            normalized,
            flags=re.UNICODE,
        )

    @staticmethod
    def _lcs_length(
        reference_tokens: list[str],
        actual_tokens: list[str],
    ) -> int:
        """
        Calculate the Longest Common Subsequence length.

        Uses dynamic programming with O(n) memory.
        """
        if not reference_tokens or not actual_tokens:
            return 0

        previous = [0] * (len(actual_tokens) + 1)

        for reference_token in reference_tokens:
            current = [0] * (len(actual_tokens) + 1)

            for index, actual_token in enumerate(actual_tokens, start=1):
                if reference_token == actual_token:
                    current[index] = previous[index - 1] + 1
                else:
                    current[index] = max(
                        previous[index],
                        current[index - 1],
                    )

            previous = current

        return previous[-1]

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Calculate deterministic ROUGE-L F1.
        """

        if expected_output is None or actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is missing.",
            )

        reference_tokens = self._tokenize(expected_output)
        actual_tokens = self._tokenize(actual_output)

        if not reference_tokens or not actual_tokens:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is empty.",
            )

        lcs_length = self._lcs_length(
            reference_tokens,
            actual_tokens,
        )

        if lcs_length == 0:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="No common subsequence between expected and actual output.",
                metadata={
                    "lcs_length": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "reference_tokens": len(reference_tokens),
                    "actual_tokens": len(actual_tokens),
                },
            )

        precision = lcs_length / len(actual_tokens)
        recall = lcs_length / len(reference_tokens)

        rouge_l = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

        return EvaluationScore(
            metric=self.name,
            score=rouge_l,
            feedback=f"ROUGE-L score: {rouge_l:.4f}.",
            metadata={
                "lcs_length": lcs_length,
                "precision": precision,
                "recall": recall,
                "reference_tokens": len(reference_tokens),
                "actual_tokens": len(actual_tokens),
            },
        )
