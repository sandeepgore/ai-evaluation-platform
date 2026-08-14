import re
import unicodedata
from typing import Any

from app.services.evaluators.base import (
    EvaluationScore,
    Evaluator,
    EvaluatorMetadata,
)


class FaithfulnessEvaluator(Evaluator):
    """
    Deterministic lexical faithfulness evaluator.

    Measures how much of the model's output contains meaningful
    terms that are also present in the supplied evaluation context.

    Formula:

        faithfulness =
            supported_output_terms / total_output_terms

    Characteristics:
        - Requires actual model output.
        - Requires supporting evaluation context.
        - Does not require expected output.
        - Does not use an LLM.
        - Does not use embeddings.
        - Uses case-insensitive token matching.
        - Normalizes Unicode using NFKC.
        - Ignores punctuation.
        - Removes common English stopwords.
        - Treats each meaningful output term once.
        - Returns a score in the range [0, 1].

    Important:
        This is lexical context support, not semantic factual
        verification.

        A high score means that the output contains many terms that
        also appear in the supplied context. It does not guarantee
        that the generated claims are logically or factually correct.

        A future semantic faithfulness evaluator should be implemented
        separately rather than changing the behavior of this evaluator.
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
        return "faithfulness"

    @property
    def metadata(self) -> EvaluatorMetadata:
        """
        Return static metadata describing the faithfulness evaluator.
        """
        return EvaluatorMetadata(
            category="faithfulness",
            description=(
                "Measures lexical support for model output terms against "
                "the supplied evaluation context using deterministic token matching."
            ),
            requires_reference=False,
            requires_context=True,
            requires_llm=False,
            applicable_to=("text",),
            tags=(
                "deterministic",
                "context-based",
                "lexical",
                "faithfulness",
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
        Return unique meaningful tokens while preserving order.

        Common stopwords are removed so generic language terms do not
        artificially influence the faithfulness calculation.
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

        Supported values:
            - string
            - list of strings
            - tuple of strings

        Multiple context chunks are joined into a single text block.
        Empty or non-string list items are ignored.
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
    def _calculate_score(
        supported_count: int,
        total_count: int,
    ) -> float:
        """
        Calculate lexical context-support score.

        Returns zero when there are no meaningful output terms.
        """
        if total_count == 0:
            return 0.0

        return supported_count / total_count

    @staticmethod
    def _build_feedback(
        supported_count: int,
        total_count: int,
        score: float,
    ) -> str:
        """
        Build deterministic human-readable feedback.
        """
        if score == 1.0:
            return "All meaningful output terms are supported by the context."

        if score == 0.0:
            return "No meaningful output terms are supported by the context."

        return (
            f"{supported_count} of {total_count} meaningful output "
            "terms are supported by the context."
        )

    async def evaluate(
        self,
        *,
        expected_output: str | None,
        actual_output: str | None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationScore:
        """
        Calculate deterministic lexical faithfulness.

        The expected output is intentionally not required.

        Faithfulness is evaluated against the supplied supporting
        context instead.
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

        score = self._calculate_score(
            supported_count,
            total_count,
        )

        feedback = self._build_feedback(
            supported_count,
            total_count,
            score,
        )

        return EvaluationScore(
            metric=self.name,
            score=score,
            feedback=feedback,
            metadata={
                "supported_tokens": supported_count,
                "unsupported_tokens": unsupported_count,
                "total_tokens": total_count,
                "supported_token_list": supported_token_list,
                "unsupported_token_list": unsupported_token_list,
                "supported_token_count": supported_count,
                "unsupported_token_count": unsupported_count,
                "output_token_count": total_count,
                "context_token_count": len(context_tokens),
            },
        )
