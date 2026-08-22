from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetCapabilities:
    """
    Aggregate capabilities available across a dataset version.

    These capabilities are used to determine which evaluation types
    and evaluators can safely be selected for the dataset.
    """

    total_cases: int

    cases_with_reference: int
    cases_without_reference: int

    cases_with_context: int
    cases_without_context: int

    has_reference: bool
    has_context: bool

    all_cases_have_reference: bool
    all_cases_have_context: bool

    reference_coverage: float
    context_coverage: float


class DatasetCapabilityAnalyzer:
    """
    Analyzes dataset cases and determines the capabilities available
    for evaluation.

    This class is intentionally independent of:
        - SQLAlchemy
        - FastAPI
        - EvaluationEngine
        - EvaluatorRegistry

    It operates only on dataset-case objects.
    """

    CONTEXT_KEYS = (
        "context",
        "retrieved_context",
        "reference_context",
    )

    @classmethod
    def analyze(
        cls,
        cases: list[Any],
    ) -> DatasetCapabilities:
        """
        Analyze a collection of dataset cases.

        Reference capability:
            A case has a reference when expected_output is a
            non-empty string.

        Context capability:
            A case has context when case_metadata contains one of:
                - context
                - retrieved_context
                - reference_context

            Supported context values:
                - non-empty string
                - non-empty list/tuple containing strings
        """

        total_cases = len(cases)

        if total_cases == 0:
            return DatasetCapabilities(
                total_cases=0,
                cases_with_reference=0,
                cases_without_reference=0,
                cases_with_context=0,
                cases_without_context=0,
                has_reference=False,
                has_context=False,
                all_cases_have_reference=False,
                all_cases_have_context=False,
                reference_coverage=0.0,
                context_coverage=0.0,
            )

        cases_with_reference = sum(1 for case in cases if cls._has_reference(case))

        cases_with_context = sum(1 for case in cases if cls._has_context(case))

        cases_without_reference = total_cases - cases_with_reference
        cases_without_context = total_cases - cases_with_context

        reference_coverage = cases_with_reference / total_cases
        context_coverage = cases_with_context / total_cases

        return DatasetCapabilities(
            total_cases=total_cases,
            cases_with_reference=cases_with_reference,
            cases_without_reference=cases_without_reference,
            cases_with_context=cases_with_context,
            cases_without_context=cases_without_context,
            has_reference=cases_with_reference > 0,
            has_context=cases_with_context > 0,
            all_cases_have_reference=cases_with_reference == total_cases,
            all_cases_have_context=cases_with_context == total_cases,
            reference_coverage=reference_coverage,
            context_coverage=context_coverage,
        )

    @staticmethod
    def _has_reference(case: Any) -> bool:
        """
        Determine whether a dataset case has a usable reference answer.
        """

        expected_output = getattr(
            case,
            "expected_output",
            None,
        )

        return isinstance(expected_output, str) and bool(expected_output.strip())

    @classmethod
    def _has_context(cls, case: Any) -> bool:
        """
        Determine whether a dataset case contains usable evaluation context.
        """

        case_metadata = getattr(
            case,
            "case_metadata",
            None,
        )

        if not isinstance(case_metadata, dict):
            return False

        for key in cls.CONTEXT_KEYS:
            value = case_metadata.get(key)

            if isinstance(value, str):
                if value.strip():
                    return True

            elif isinstance(value, (list, tuple)):
                if any(isinstance(item, str) and item.strip() for item in value):
                    return True

        return False
