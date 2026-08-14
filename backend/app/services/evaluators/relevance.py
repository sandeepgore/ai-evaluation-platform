import re
import unicodedata
from typing import Any

from app.services.evaluators.base import EvaluationScore, Evaluator


class RelevanceEvaluator(Evaluator):
    """
    Keyword-based relevance evaluator.

    Compares the important terms in the input/query with the actual
    model output.

    This is a lightweight lexical relevance metric. It does not use
    embeddings or an LLM judge.
    """

    # Common English stopwords that should not influence lexical relevance.
    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    @property
    def name(self) -> str:
        return "relevance"

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize Unicode and casing.
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

    @classmethod
    def _meaningful_tokens(cls, text: str) -> list[str]:
        """
        Return unique meaningful tokens with common stopwords removed.

        Order is preserved so metadata remains deterministic.
        """
        tokens = cls._tokenize(text)

        return list(dict.fromkeys(token for token in tokens if token not in cls.STOPWORDS))

    @classmethod
    def _relevance_tokens(cls, text: str) -> list[str]:
        """
        Extract terms that carry relevance information.

        Stopwords are removed, while meaningful lexical terms are kept.
        """
        return cls._meaningful_tokens(text)

    @staticmethod
    def _calculate_overlap(
        query_tokens: list[str],
        actual_tokens: list[str],
    ) -> list[str]:
        """
        Return unique query terms that occur in the actual output.
        """
        actual_token_set = set(actual_tokens)

        return [token for token in query_tokens if token in actual_token_set]

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
                feedback="Input or actual output is empty.",
            )

        if not context:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback=("Input or query is missing from evaluation context."),
            )

        input_text = context.get("input") or context.get("query")

        if not isinstance(input_text, str) or not input_text.strip():
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback=("Input or query is missing from evaluation context."),
            )

        query_tokens = self._relevance_tokens(input_text)
        actual_tokens = self._relevance_tokens(actual_output)

        if not query_tokens or not actual_tokens:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Input or actual output is empty.",
                metadata={
                    "query_tokens": query_tokens,
                    "actual_tokens": actual_tokens,
                    "overlap_tokens": 0,
                },
            )

        overlap = self._calculate_overlap(
            query_tokens,
            actual_tokens,
        )

        overlap_count = len(overlap)

        # Relevance is measured as the proportion of meaningful query
        # concepts covered by the answer.
        score = overlap_count / len(query_tokens)

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=f"Lexical relevance score: {score:.4f}.",
            metadata={
                "query_tokens": query_tokens,
                "actual_tokens": actual_tokens,
                "overlap": overlap,
                "overlap_tokens": overlap_count,
                "query_token_count": len(query_tokens),
                "actual_token_count": len(actual_tokens),
            },
        )
