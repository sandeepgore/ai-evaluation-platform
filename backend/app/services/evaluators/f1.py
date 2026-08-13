import re
import unicodedata
from collections import Counter
from typing import Any

from app.services.evaluators.base import EvaluationScore, Evaluator


class F1Evaluator(Evaluator):
    @property
    def name(self) -> str:
        return "f1"

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

        expected_tokens = self._tokenize(expected_output)
        actual_tokens = self._tokenize(actual_output)

        if not expected_tokens or not actual_tokens:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output or actual output is empty.",
            )

        expected_counts = Counter(expected_tokens)
        actual_counts = Counter(actual_tokens)

        common_tokens = expected_counts & actual_counts
        overlap = sum(common_tokens.values())

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

        precision = overlap / len(actual_tokens)
        recall = overlap / len(expected_tokens)

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )

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
