from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JudgeResult:
    """
    Structured result returned by the LLM judge.
    """

    score: float

    feedback: str | None = None

    reasoning: str | None = None

    metadata: dict[str, Any] | None = None

    raw_output: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Judge score must be between 0 and 1, got {self.score}.")
