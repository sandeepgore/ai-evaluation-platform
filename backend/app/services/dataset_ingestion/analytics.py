from dataclasses import dataclass


@dataclass
class DatasetAnalyticsAccumulator:
    case_count: int = 0
    reference_count: int = 0
    context_count: int = 0

    def observe(
        self,
        *,
        has_reference: bool,
        has_context: bool,
    ) -> None:
        self.case_count += 1

        if has_reference:
            self.reference_count += 1

        if has_context:
            self.context_count += 1

    def to_dict(self) -> dict[str, int | float]:
        reference_coverage = self.reference_count / self.case_count if self.case_count else 0.0

        context_coverage = self.context_count / self.case_count if self.case_count else 0.0

        return {
            "case_count": self.case_count,
            "reference_count": self.reference_count,
            "context_count": self.context_count,
            "reference_coverage": reference_coverage,
            "context_coverage": context_coverage,
        }
