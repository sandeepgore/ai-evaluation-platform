import re
import unicodedata
from typing import Any

from app.services.evaluators.base import EvaluationScore, Evaluator


class FaithfulnessEvaluator(Evaluator):
    """
    Deterministic lexical faithfulness evaluator.

    Measures how much of the actual output is supported by the
    provided evaluation context.

    This is a lightweight deterministic metric. It does not use
    an LLM or embeddings.
    """

    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "for",
        "from",
        "has",
        "have",
        "had",
        "he",
        "her",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "there",
        "this",
        "to",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "you",
        "your",
    }

    @property
    def name(self) -> str:
        return "faithfulness"

    @staticmethod
    def _normalize_text(text: str) -> str:
        return unicodedata.normalize("NFKC", text).lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        normalized = cls._normalize_text(text)

        return re.findall(
            r"\b\w+\b",
            normalized,
            flags=re.UNICODE,
        )

    @classmethod
    def _meaningful_tokens(cls, text: str) -> list[str]:
        """
        Return unique meaningful tokens while preserving order.

        Stopwords are removed so generic language terms do not
        artificially increase faithfulness.
        """
        tokens = cls._tokenize(text)

        return list(dict.fromkeys(token for token in tokens if token not in cls.STOPWORDS))

    @staticmethod
    def _get_context_text(
        context: dict[str, Any],
    ) -> str | None:
        """
        Extract supporting context from supported context formats.

        Supported keys:
        - context
        - retrieved_context
        - reference_context

        Values may be either:
        - a string
        - a list/tuple of strings
        """

        for key in (
            "context",
            "retrieved_context",
            "reference_context",
        ):
            value = context.get(key)

            if isinstance(value, str):
                if value.strip():
                    return value

            elif isinstance(value, (list, tuple)):
                parts = [item.strip() for item in value if isinstance(item, str) and item.strip()]

                if parts:
                    return " ".join(parts)

        return None

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:

        if actual_output is None:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Actual output is missing.",
            )

        if not actual_output.strip():
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Context or actual output is empty.",
            )

        if not context:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Context is missing from evaluation context.",
            )

        context_text = self._get_context_text(context)

        if not context_text:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Context is missing from evaluation context.",
            )

        output_tokens = self._meaningful_tokens(actual_output)
        context_tokens = self._meaningful_tokens(context_text)

        if not output_tokens or not context_tokens:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Context or actual output is empty.",
            )

        context_token_set = set(context_tokens)

        supported_token_list = [token for token in output_tokens if token in context_token_set]

        unsupported_token_list = [
            token for token in output_tokens if token not in context_token_set
        ]

        supported_count = len(supported_token_list)
        unsupported_count = len(unsupported_token_list)
        total_count = len(output_tokens)

        score = supported_count / total_count if total_count > 0 else 0.0

        if score == 1.0:
            feedback = "All meaningful output terms are supported by the context."
        elif score == 0.0:
            feedback = "No meaningful output terms are supported by the context."
        else:
            feedback = (
                f"{supported_count} of {total_count} meaningful output "
                "terms are supported by the context."
            )

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=feedback,
            metadata={
                # Numeric counts used by consumers/tests.
                "supported_tokens": supported_count,
                "unsupported_tokens": unsupported_count,
                "total_tokens": total_count,
                # Explicit token lists for debugging/inspection.
                "supported_token_list": supported_token_list,
                "unsupported_token_list": unsupported_token_list,
                "supported_token_count": supported_count,
                "unsupported_token_count": unsupported_count,
                "output_token_count": total_count,
                "context_token_count": len(context_tokens),
            },
        )
