import math
import re
import unicodedata
from collections import Counter
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class BLEUEvaluator(Evaluator):
    """
    Deterministic BLEU-4 evaluator for comparing generated text
    against a single reference answer.

    Characteristics:
        - Requires expected/reference output.
        - Does not require evaluation context.
        - Does not use an LLM.
        - Does not use embeddings.
        - Uses case-insensitive token matching.
        - Normalizes Unicode using NFKC.
        - Ignores punctuation during tokenization.
        - Uses clipped n-gram counts.
        - Uses unsmoothed BLEU-4.
    """

    @property
    def name(self) -> str:
        """Return the unique evaluator name."""
        return "bleu"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing the BLEU evaluator.
        """
        return EvaluatorMetadata(
            category="similarity",
            description=(
                "Measures n-gram overlap between the model output and "
                "the reference answer using deterministic BLEU-4 scoring."
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
                "n-gram",
                "bleu",
            ),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text before tokenization.

        Normalization:
            1. Unicode NFKC normalization.
            2. Lowercase conversion.

        Punctuation is removed during tokenization.
        """
        return unicodedata.normalize("NFKC", text).lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """
        Tokenize normalized text while ignoring punctuation.
        """
        normalized = cls._normalize_text(text)

        return re.findall(
            r"\b\w+\b",
            normalized,
            flags=re.UNICODE,
        )

    @staticmethod
    def _ngrams(
        tokens: list[str],
        n: int,
    ) -> Counter[tuple[str, ...]]:
        """
        Generate n-gram frequency counts.
        """
        if len(tokens) < n:
            return Counter()

        return Counter(tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1))

    @classmethod
    def _modified_precision(
        cls,
        reference_tokens: list[str],
        actual_tokens: list[str],
        n: int,
    ) -> tuple[int, int]:
        """
        Calculate clipped n-gram precision.
        """
        actual_ngrams = cls._ngrams(actual_tokens, n)
        reference_ngrams = cls._ngrams(reference_tokens, n)

        if not actual_ngrams:
            return 0, 0

        matched = sum(min(count, reference_ngrams[ngram]) for ngram, count in actual_ngrams.items())

        total = sum(actual_ngrams.values())

        return matched, total

    @staticmethod
    def _calculate_brevity_penalty(
        reference_length: int,
        actual_length: int,
    ) -> float:
        """
        Calculate the BLEU brevity penalty.
        """
        if actual_length >= reference_length:
            return 1.0

        return math.exp(
            1 - reference_length / actual_length,
        )

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Calculate deterministic unsmoothed BLEU-4.
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

        precisions: dict[str, float] = {}
        matched_counts: dict[str, int] = {}
        total_counts: dict[str, int] = {}

        for n in range(1, 5):
            matched, total = self._modified_precision(
                reference_tokens,
                actual_tokens,
                n,
            )

            gram_name = f"{n}-gram"

            matched_counts[gram_name] = matched
            total_counts[gram_name] = total
            precisions[gram_name] = matched / total if total > 0 else 0.0

        reference_length = len(reference_tokens)
        actual_length = len(actual_tokens)

        brevity_penalty = self._calculate_brevity_penalty(
            reference_length,
            actual_length,
        )

        if any(value == 0.0 for value in precisions.values()):
            bleu_score = 0.0
        else:
            log_precision_sum = sum(math.log(value) for value in precisions.values())

            geometric_mean = math.exp(
                log_precision_sum / 4,
            )

            bleu_score = brevity_penalty * geometric_mean

        return EvaluationScore(
            metric=self.name,
            score=bleu_score,
            feedback=f"BLEU-4 score: {bleu_score:.4f}.",
            metadata={
                "precisions": precisions,
                "matched_counts": matched_counts,
                "total_counts": total_counts,
                "brevity_penalty": brevity_penalty,
                "reference_length": reference_length,
                "actual_length": actual_length,
                "normalization": {
                    "unicode": "NFKC",
                    "lowercase": True,
                    "ignore_punctuation": True,
                },
            },
        )
