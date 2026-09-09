from typing import Any


CONTEXT_KEYS = (
    "context",
    "retrieved_context",
    "reference_context",
)


def derive_case_capabilities(
    *,
    expected_output: str | None,
    case_metadata: dict[str, Any] | None,
) -> tuple[bool, bool]:
    """
    Derive persisted dataset-case capability flags from case content.

    has_reference:
        True when expected_output is present.

    has_context:
        True when supported context metadata contains either:
        - a non-empty string, or
        - a list/tuple containing at least one non-empty string.
    """
    has_reference = expected_output is not None

    has_context = False

    if isinstance(case_metadata, dict):
        for key in CONTEXT_KEYS:
            value = case_metadata.get(key)

            if isinstance(value, str):
                if value.strip():
                    has_context = True
                    break

            elif isinstance(value, (list, tuple)):
                if any(isinstance(item, str) and item.strip() for item in value):
                    has_context = True
                    break

    return has_reference, has_context
