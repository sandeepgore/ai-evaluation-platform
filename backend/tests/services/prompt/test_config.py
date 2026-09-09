import pytest
from pydantic import ValidationError

from app.services.prompt.config import PromptConfig, PromptMode


class TestPromptConfig:
    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------

    def test_default_configuration_is_simple(self):
        config = PromptConfig()

        assert config.mode == PromptMode.SIMPLE
        assert config.instruction is None
        assert config.system is None
        assert config.user_template is None

    # ------------------------------------------------------------------
    # Simple mode
    # ------------------------------------------------------------------

    def test_simple_mode_accepts_instruction(self):
        config = PromptConfig(
            mode=PromptMode.SIMPLE,
            instruction="Answer concisely.",
        )

        assert config.mode == PromptMode.SIMPLE
        assert config.instruction == "Answer concisely."

    def test_simple_mode_rejects_system_prompt(self):
        with pytest.raises(
            ValidationError,
            match="Simple prompt mode only supports 'instruction'",
        ):
            PromptConfig(
                mode=PromptMode.SIMPLE,
                system="You are an assistant.",
            )

    def test_simple_mode_rejects_user_template(self):
        with pytest.raises(
            ValidationError,
            match="Simple prompt mode only supports 'instruction'",
        ):
            PromptConfig(
                mode=PromptMode.SIMPLE,
                user_template="{{input}}",
            )

    def test_simple_mode_rejects_system_and_user_template(self):
        with pytest.raises(
            ValidationError,
            match="Simple prompt mode only supports 'instruction'",
        ):
            PromptConfig(
                mode=PromptMode.SIMPLE,
                system="You are an assistant.",
                user_template="{{input}}",
            )

    # ------------------------------------------------------------------
    # Advanced mode
    # ------------------------------------------------------------------

    def test_advanced_mode_accepts_system(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="You are an assistant.",
        )

        assert config.mode == PromptMode.ADVANCED
        assert config.system == "You are an assistant."

    def test_advanced_mode_accepts_user_template(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Question: {{input}}",
        )

        assert config.mode == PromptMode.ADVANCED
        assert config.user_template == "Question: {{input}}"

    def test_advanced_mode_accepts_system_and_user_template(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="You are an assistant.",
            user_template="Question: {{input}}",
        )

        assert config.system == "You are an assistant."
        assert config.user_template == "Question: {{input}}"

    def test_advanced_mode_rejects_instruction(self):
        with pytest.raises(
            ValidationError,
            match="Advanced prompt mode does not support 'instruction'",
        ):
            PromptConfig(
                mode=PromptMode.ADVANCED,
                instruction="Answer concisely.",
            )

    def test_advanced_mode_rejects_instruction_with_system(self):
        with pytest.raises(
            ValidationError,
            match="Advanced prompt mode does not support 'instruction'",
        ):
            PromptConfig(
                mode=PromptMode.ADVANCED,
                instruction="Answer concisely.",
                system="You are an assistant.",
            )

    # ------------------------------------------------------------------
    # Mode parsing
    # ------------------------------------------------------------------

    def test_simple_mode_accepts_string_value(self):
        config = PromptConfig(
            mode="simple",
            instruction="Answer concisely.",
        )

        assert config.mode == PromptMode.SIMPLE

    def test_advanced_mode_accepts_string_value(self):
        config = PromptConfig(
            mode="advanced",
            user_template="{{input}}",
        )

        assert config.mode == PromptMode.ADVANCED

    def test_invalid_mode_is_rejected(self):
        with pytest.raises(ValidationError):
            PromptConfig(
                mode="invalid",
            )

    # ------------------------------------------------------------------
    # Field length limits
    # ------------------------------------------------------------------

    def test_instruction_has_maximum_length(self):
        with pytest.raises(ValidationError):
            PromptConfig(
                instruction="a" * 10_001,
            )

    def test_system_prompt_has_maximum_length(self):
        with pytest.raises(ValidationError):
            PromptConfig(
                mode=PromptMode.ADVANCED,
                system="a" * 10_001,
            )

    def test_user_template_has_maximum_length(self):
        with pytest.raises(ValidationError):
            PromptConfig(
                mode=PromptMode.ADVANCED,
                user_template="a" * 10_001,
            )

    def test_instruction_at_maximum_length_is_valid(self):
        config = PromptConfig(
            instruction="a" * 10_000,
        )

        assert len(config.instruction) == 10_000

    def test_system_prompt_at_maximum_length_is_valid(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="a" * 10_000,
        )

        assert len(config.system) == 10_000

    def test_user_template_at_maximum_length_is_valid(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="a" * 10_000,
        )

        assert len(config.user_template) == 10_000

    # ------------------------------------------------------------------
    # JSON / serialization
    # ------------------------------------------------------------------

    def test_configuration_can_be_serialized(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="You are an assistant.",
            user_template="Question: {{input}}",
        )

        data = config.model_dump()

        assert data == {
            "mode": PromptMode.ADVANCED,
            "instruction": None,
            "system": "You are an assistant.",
            "user_template": "Question: {{input}}",
        }

    def test_configuration_can_be_created_from_run_configuration_shape(self):
        config = PromptConfig.model_validate(
            {
                "mode": "advanced",
                "system": "You are an assistant.",
                "user_template": "Question: {{input}}",
            }
        )

        assert config.mode == PromptMode.ADVANCED
        assert config.system == "You are an assistant."
        assert config.user_template == "Question: {{input}}"
