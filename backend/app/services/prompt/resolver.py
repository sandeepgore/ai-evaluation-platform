import re
from typing import Any

from app.services.prompt.config import PromptConfig, PromptMode


class PromptResolutionError(ValueError):
    """Raised when a prompt cannot be safely resolved."""


class PromptResolver:
    """Resolve an evaluation-run prompt into a model-ready prompt."""

    _VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

    _SUPPORTED_VARIABLES = {
        "input",
        "context",
    }

    @classmethod
    def resolve(
        cls,
        *,
        config: PromptConfig | None,
        case_input: str,
        context: Any = None,
    ) -> str:
        """
        Resolve a prompt configuration for a single evaluation case.

        When no prompt configuration is provided, the original case input
        is returned unchanged.
        """
        if config is None:
            return case_input

        if config.mode == PromptMode.SIMPLE:
            return cls._resolve_simple(
                config=config,
                case_input=case_input,
                context=context,
            )

        if config.mode == PromptMode.ADVANCED:
            return cls._resolve_advanced(
                config=config,
                case_input=case_input,
                context=context,
            )

        raise PromptResolutionError(f"Unsupported prompt mode: {config.mode}")

    @classmethod
    def _resolve_simple(
        cls,
        *,
        config: PromptConfig,
        case_input: str,
        context: Any,
    ) -> str:
        instruction = config.instruction or ""

        if not instruction:
            return case_input

        return f"{instruction}\n\n{case_input}"

    @classmethod
    def _resolve_advanced(
        cls,
        *,
        config: PromptConfig,
        case_input: str,
        context: Any,
    ) -> str:
        parts: list[str] = []

        if config.system:
            parts.append(
                cls._render(
                    config.system,
                    case_input=case_input,
                    context=context,
                )
            )

        if config.user_template:
            parts.append(
                cls._render(
                    config.user_template,
                    case_input=case_input,
                    context=context,
                )
            )

        if not parts:
            return case_input

        return "\n\n".join(parts)

    @classmethod
    def _render(
        cls,
        template: str,
        *,
        case_input: str,
        context: Any,
    ) -> str:
        variables = cls._VARIABLE_PATTERN.findall(template)

        unsupported = set(variables) - cls._SUPPORTED_VARIABLES

        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise PromptResolutionError(f"Unsupported prompt variable(s): {names}")

        values = {
            "input": case_input,
            "context": cls._format_context(context),
        }

        return cls._VARIABLE_PATTERN.sub(
            lambda match: values[match.group(1)],
            template,
        )

    @staticmethod
    def _format_context(context: Any) -> str:
        if context is None:
            return ""

        if isinstance(context, str):
            return context

        if isinstance(context, (list, tuple)):
            return "\n".join(str(item) for item in context)

        return str(context)
