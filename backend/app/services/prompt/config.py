from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class PromptMode(StrEnum):
    SIMPLE = "simple"
    ADVANCED = "advanced"


class PromptConfig(BaseModel):
    """
    Configuration for an evaluation-run prompt.

    Prompt configuration controls how the model is instructed.
    It does not control evaluator applicability or output validation.
    """

    mode: PromptMode = PromptMode.SIMPLE

    instruction: str | None = Field(
        default=None,
        max_length=10_000,
    )

    system: str | None = Field(
        default=None,
        max_length=10_000,
    )

    user_template: str | None = Field(
        default=None,
        max_length=10_000,
    )

    @model_validator(mode="after")
    def validate_mode_configuration(self) -> "PromptConfig":
        if self.mode == PromptMode.SIMPLE:
            if self.system is not None or self.user_template is not None:
                raise ValueError("Simple prompt mode only supports 'instruction'.")

        if self.mode == PromptMode.ADVANCED:
            if self.instruction is not None:
                raise ValueError(
                    "Advanced prompt mode does not support 'instruction'. "
                    "Use 'system' and/or 'user_template'."
                )

        return self
