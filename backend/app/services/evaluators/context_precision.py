import re
import unicodedata
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class ContextPrecisionEvaluator(Evaluator):
    """Deterministic lexical context precision evaluator.

    Measures how much of the supplied evaluation context contains
    meaningful terms that are also represented in the expected/reference
    answer.

    Formula:

        context_precision =
            context terms supported by reference
            ---------------------------------
                total meaningful context terms

    Characteristics:
        - Requires expected/reference output.
        - Requires supporting evaluation context.
        - Does not require actual model output.
        - Does not use an LLM.
        - Does not use embeddings.
        - Uses case-insensitive token matching.
        - Normalizes Unicode using NFKC.
        - Ignores punctuation.
        - Removes common English stopwords.
        - Treats each meaningful term once.
        - Returns a score in the range [0, 1].

    Important:
        This is lexical context precision, not semantic retrieval
        precision.

        A high score means that many meaningful terms in the retrieved
        context also appear in the expected answer. It does not guarantee
        that the retrieved context is semantically relevant or correctly
        ordered.

        A future semantic/LLM-based context precision evaluator should
        be implemented separately.
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
        """Return the unique evaluator name."""
        return "context_precision"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """Return static metadata describing the evaluator."""
        return EvaluatorMetadata(
            category="context_precision",
            description=(
                "Measures lexical precision of meaningful context terms "
                "against the expected reference answer."
            ),
            required_inputs=(
                "expected_output",
                "context",
            ),
            requires_reference=True,
            requires_context=True,
            requires_supporting_context=True,
            requires_llm=False,
            applicable_to=("rag",),
            tags=(
                "deterministic",
                "context-based",
                "lexical",
                "retrieval",
                "precision",
            ),
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize Unicode and casing."""
        return unicodedata.normalize("NFKC", text).lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """Tokenize text while ignoring punctuation."""
        normalized = cls._normalize_text(text)

        return re.findall(
            r"\b\w+\b",
            normalized,
            flags=re.UNICODE,
        )

    @classmethod
    def _meaningful_tokens(cls, text: str) -> list[str]:
        """Return unique meaningful tokens while preserving order."""
        tokens = cls._tokenize(text)

        return list(dict.fromkeys(token for token in tokens if token not in cls.STOPWORDS))

    @staticmethod
    def _get_context_text(
        context: dict[str, Any],
    ) -> str | None:
        """Extract supporting context from supported context formats.

        Supported keys:
            - context
            - retrieved_context
            - reference_context

        Supported values:
            - string
            - list of strings
            - tuple of strings
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

    @staticmethod
    def _calculate_overlap(
        context_tokens: list[str],
        reference_tokens: list[str],
    ) -> list[str]:
        """Return context terms represented in the reference answer."""
        reference_token_set = set(reference_tokens)

        return [token for token in context_tokens if token in reference_token_set]

    @staticmethod
    def _calculate_score(
        overlap_count: int,
        context_token_count: int,
    ) -> float:
        """Calculate lexical context precision."""
        if context_token_count == 0:
            return 0.0

        return overlap_count / context_token_count

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """Calculate deterministic lexical context precision.

        The actual output is intentionally not required because this
        evaluator measures whether retrieved context terms are
        represented in the expected answer.
        """
        if not expected_output or not expected_output.strip():
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Expected output is missing.",
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

        reference_tokens = self._meaningful_tokens(expected_output)
        context_tokens = self._meaningful_tokens(context_text)

        if not reference_tokens or not context_tokens:
            return EvaluationScore(
                metric=self.name,
                score=0.0,
                feedback="Context or expected output is empty.",
                metadata={
                    "reference_tokens": reference_tokens,
                    "context_tokens": context_tokens,
                    "overlap": [],
                    "overlap_tokens": 0,
                    "reference_token_count": len(reference_tokens),
                    "context_token_count": len(context_tokens),
                },
            )

        overlap = self._calculate_overlap(
            context_tokens,
            reference_tokens,
        )

        overlap_count = len(overlap)

        score = self._calculate_score(
            overlap_count,
            len(context_tokens),
        )

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=f"Lexical context precision score: {score:.4f}.",
            metadata={
                "reference_tokens": reference_tokens,
                "context_tokens": context_tokens,
                "overlap": overlap,
                "overlap_tokens": overlap_count,
                "reference_token_count": len(reference_tokens),
                "context_token_count": len(context_tokens),
            },
        )
