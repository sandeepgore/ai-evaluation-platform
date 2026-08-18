import re
import unicodedata
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class RelevanceEvaluator(Evaluator):
    """
    Deterministic lexical relevance evaluator.

    Measures how much of the user's input/query is covered by
    meaningful terms in the model output.

    Formula:

        relevance = overlapping_query_terms / query_terms

    Characteristics:
        - Requires actual model output.
        - Requires input/query in evaluation context.
        - Does not require expected output.
        - Does not use an LLM.
        - Does not use embeddings.
        - Uses case-insensitive token matching.
        - Normalizes Unicode using NFKC.
        - Ignores punctuation.
        - Removes common English stopwords.
        - Treats each meaningful query term once.
        - Returns a score in the range [0, 1].

    Important:
        This is lexical relevance, not semantic relevance.

        A future semantic/LLM-based relevance evaluator should be
        implemented as a separate evaluator rather than changing
        this evaluator's existing behavior.
    """

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
        """Return the unique evaluator name."""
        return "relevance"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing the relevance evaluator.
        """
        return EvaluatorMetadata(
            category="relevance",
            description=(
                "Measures lexical coverage of meaningful query terms "
                "in the model output using deterministic token overlap."
            ),
            required_inputs=(
                "actual_output",
                "context",
            ),
            requires_reference=False,
            requires_context=True,
            requires_llm=False,
            applicable_to=("text",),
            tags=(
                "deterministic",
                "context-based",
                "lexical",
                "relevance",
            ),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize Unicode and casing.
        """
        return unicodedata.normalize(
            "NFKC",
            text,
        ).lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """
        Tokenize text while ignoring punctuation.

        The tokenizer is deterministic and Unicode-aware.
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
        Extract unique meaningful tokens.

        Common stopwords are removed.

        Token order is preserved so that metadata remains
        deterministic and easy to inspect.
        """
        tokens = cls._tokenize(text)

        return list(dict.fromkeys(token for token in tokens if token not in cls.STOPWORDS))

    @classmethod
    def _relevance_tokens(cls, text: str) -> list[str]:
        """
        Extract lexical terms used for relevance calculation.
        """
        return cls._meaningful_tokens(text)

    @staticmethod
    def _calculate_overlap(
        query_tokens: list[str],
        actual_tokens: list[str],
    ) -> list[str]:
        """
        Return unique query terms present in the actual output.

        Query-token order is preserved.
        """
        actual_token_set = set(actual_tokens)

        return [token for token in query_tokens if token in actual_token_set]

    @staticmethod
    def _calculate_score(
        overlap_count: int,
        query_token_count: int,
    ) -> float:
        """
        Calculate lexical query coverage.

        Returns zero when there are no meaningful query terms.
        """
        if query_token_count == 0:
            return 0.0

        return overlap_count / query_token_count

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Calculate deterministic lexical relevance.

        The expected output is intentionally not required because
        relevance evaluates whether the generated answer addresses
        terms present in the input/query.
        """

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
                feedback="Input or query is missing from evaluation context.",
            )

        input_text = context.get("input") or context.get("query")

        if not isinstance(input_text, str) or not input_text.strip():
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Input or query is missing from evaluation context.",
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

        score = self._calculate_score(
            overlap_count,
            len(query_tokens),
        )

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
