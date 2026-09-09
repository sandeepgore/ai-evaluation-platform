import pytest

from app.services.prompt.config import PromptConfig, PromptMode
from app.services.prompt.resolver import (
    PromptResolutionError,
    PromptResolver,
)


class TestPromptResolver:
    # ------------------------------------------------------------------
    # No prompt
    # ------------------------------------------------------------------

    def test_no_prompt_returns_case_input_unchanged(self):
        result = PromptResolver.resolve(
            config=None,
            case_input="What is RAG?",
        )

        assert result == "What is RAG?"

    # ------------------------------------------------------------------
    # Simple mode
    # ------------------------------------------------------------------

    def test_simple_prompt_appends_instruction_before_input(self):
        config = PromptConfig(
            mode=PromptMode.SIMPLE,
            instruction="Answer concisely.",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == ("Answer concisely.\n\nWhat is RAG?")

    def test_simple_prompt_without_instruction_returns_input(self):
        config = PromptConfig(
            mode=PromptMode.SIMPLE,
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "What is RAG?"

    def test_simple_prompt_does_not_require_context(self):
        config = PromptConfig(
            mode=PromptMode.SIMPLE,
            instruction="Answer the question.",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context=None,
        )

        assert result == ("Answer the question.\n\nWhat is RAG?")

    # ------------------------------------------------------------------
    # Advanced mode
    # ------------------------------------------------------------------

    def test_advanced_system_prompt_is_rendered(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="You are a helpful assistant.",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "You are a helpful assistant."

    def test_advanced_user_template_is_rendered(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Question: {{input}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "Question: What is RAG?"

    def test_advanced_system_and_user_template_are_combined(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="You are a helpful assistant.",
            user_template="Question: {{input}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == ("You are a helpful assistant.\n\nQuestion: What is RAG?")

    def test_advanced_prompt_without_templates_returns_input(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "What is RAG?"

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def test_input_variable_is_replaced(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Answer this question: {{input}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "Answer this question: What is RAG?"

    def test_context_variable_is_replaced(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template=("Question: {{input}}\nContext: {{context}}"),
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context="RAG retrieves relevant documents.",
        )

        assert result == ("Question: What is RAG?\nContext: RAG retrieves relevant documents.")

    def test_input_and_context_can_be_used_multiple_times(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template=("{{input}}\n{{input}}\n{{context}}\n{{context}}"),
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context="Retrieved documents.",
        )

        assert result == ("What is RAG?\nWhat is RAG?\nRetrieved documents.\nRetrieved documents.")

    def test_variable_whitespace_is_supported(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Question: {{  input  }}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "Question: What is RAG?"

    # ------------------------------------------------------------------
    # Missing context
    # ------------------------------------------------------------------

    def test_missing_context_resolves_to_empty_string(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template=("Question: {{input}}\nContext: {{context}}"),
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context=None,
        )

        assert result == ("Question: What is RAG?\nContext: ")

    def test_empty_context_resolves_to_empty_string(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Context: {{context}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context="",
        )

        assert result == "Context: "

    def test_list_context_is_rendered(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Context:\n{{context}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context=[
                "Document one.",
                "Document two.",
            ],
        )

        assert result == ("Context:\nDocument one.\nDocument two.")

    def test_tuple_context_is_rendered(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Context:\n{{context}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context=(
                "Document one.",
                "Document two.",
            ),
        )

        assert result == ("Context:\nDocument one.\nDocument two.")

    # ------------------------------------------------------------------
    # Variable safety
    # ------------------------------------------------------------------

    def test_unknown_variable_is_rejected(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Question: {{unknown_variable}}",
        )

        with pytest.raises(
            PromptResolutionError,
            match="Unsupported prompt variable",
        ):
            PromptResolver.resolve(
                config=config,
                case_input="What is RAG?",
            )

    def test_expected_output_variable_is_rejected(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Expected answer: {{expected_output}}",
        )

        with pytest.raises(
            PromptResolutionError,
            match="expected_output",
        ):
            PromptResolver.resolve(
                config=config,
                case_input="What is RAG?",
            )

    def test_multiple_unsupported_variables_are_reported(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template=("{{expected_output}} {{unknown_variable}}"),
        )

        with pytest.raises(
            PromptResolutionError,
            match="expected_output.*unknown_variable",
        ):
            PromptResolver.resolve(
                config=config,
                case_input="What is RAG?",
            )

    # ------------------------------------------------------------------
    # Empty values
    # ------------------------------------------------------------------

    def test_empty_case_input_is_preserved_by_resolver(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            user_template="Question: {{input}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="",
        )

        assert result == "Question: "

    def test_empty_system_prompt_is_ignored(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="",
            user_template="Question: {{input}}",
        )

        result = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
        )

        assert result == "Question: What is RAG?"

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_same_inputs_produce_same_prompt(self):
        config = PromptConfig(
            mode=PromptMode.ADVANCED,
            system="You are an assistant.",
            user_template=("Question: {{input}}\nContext: {{context}}"),
        )

        first = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context="Retrieved documents.",
        )

        second = PromptResolver.resolve(
            config=config,
            case_input="What is RAG?",
            context="Retrieved documents.",
        )

        assert first == second
