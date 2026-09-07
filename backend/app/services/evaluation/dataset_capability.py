from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetCapabilities:
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
    @classmethod
    def analyze(cls, cases: list[Any]) -> DatasetCapabilities:
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

        cases_with_reference = sum(1 for case in cases if case.has_reference)

        cases_with_context = sum(1 for case in cases if case.has_context)

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
