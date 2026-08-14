import math
import re
import unicodedata
from collections import Counter
from typing import Any

from app.services.evaluators.base import EvaluationScore, Evaluator


class BLEUEvaluator(Evaluator):
    """
    BLEU-4 evaluator for comparing generated text against a reference.

    Uses:
    - 1-gram through 4-gram modified precision
    - geometric mean of n-gram precisions
    - brevity penalty
    """

    @property
    def name(self) -> str:
        return "bleu"

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
        return re.findall(r"\b\w+\b", normalized, flags=re.UNICODE)

    @staticmethod
    def _ngrams(tokens: list[str], n: int) -> Counter[tuple[str, ...]]:
        """
        Generate n-gram counts.
        """
        if len(tokens) < n:
            return Counter()

        return Counter(
            tuple(tokens[index : index + n])
            for index in range(len(tokens) - n + 1)
        )

    @classmethod
    def _modified_precision(
        cls,
        reference_tokens: list[str],
        actual_tokens: list[str],
        n: int,
    ) -> tuple[int, int]:
        """
        Calculate clipped n-gram precision.

        Returns:
            (matched_count, total_candidate_ngrams)
        """
        actual_ngrams = cls._ngrams(actual_tokens, n)
        reference_ngrams = cls._ngrams(reference_tokens, n)

        if not actual_ngrams:
            return 0, 0

        matched = sum(
            min(count, reference_ngrams[ngram])
            for ngram, count in actual_ngrams.items()
        )

        total = sum(actual_ngrams.values())

        return matched, total

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

            matched_counts[f"{n}-gram"] = matched
            total_counts[f"{n}-gram"] = total

            precisions[f"{n}-gram"] = (
                matched / total
                if total > 0
                else 0.0
            )

        if any(value == 0.0 for value in precisions.values()):
            bleu_score = 0.0
        else:
            log_precision_sum = sum(
                math.log(value)
                for value in precisions.values()
            )

            geometric_mean = math.exp(log_precision_sum / 4)

            reference_length = len(reference_tokens)
            actual_length = len(actual_tokens)

            brevity_penalty = (
                1.0
                if actual_length >= reference_length
                else math.exp(1 - reference_length / actual_length)
            )

            bleu_score = brevity_penalty * geometric_mean

        reference_length = len(reference_tokens)
        actual_length = len(actual_tokens)

        brevity_penalty = (
            1.0
            if actual_length >= reference_length
            else math.exp(1 - reference_length / actual_length)
        )

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
            },
        )
