# Shared Library

## Overview

The Shared Library contains reusable components that are used across multiple services of the AI Evaluation Platform.

It provides common:

- Constants
- Types
- Exceptions
- Utilities
- Validation helpers

The goal is to reduce duplication and maintain consistency across the platform.

---

# Architecture

```
                  Backend


                     |


                     |


              Shared Library


                     |


      --------------------------------


      |              |               |


 Evaluation     Gateway        Workers


```

---

# Directory Structure

```
shared/


├── constants/


├── exceptions/


├── types/


└── utils/


```

---

# Components

## Constants

Contains platform-wide constants.

Examples:

```
STATUS_CODES

EVALUATION_TYPES

MODEL_TYPES

```

Usage:

```python
from shared.constants import EvaluationStatus

```

---

# Types

Contains common type definitions.

Examples:

```
EvaluationResult

ModelResponse

UserContext

```

Purpose:

- Type consistency
- Better IDE support
- Safer development

---

# Exceptions

Centralized application exceptions.

Examples:

```
AuthenticationError

ValidationError

ModelProviderError

EvaluationError

```

Benefits:

- Consistent error handling
- Easier debugging
- Better API responses

---

# Utilities

Reusable helper functions.

Examples:

```
date utilities

formatters

validators

logging helpers

```

---

# Usage

Services import shared components:

Example:

```python
from shared.exceptions import EvaluationError

from shared.types import EvaluationResult

```

---

# Development Guidelines

When adding shared code:

## Keep It Generic

Shared components should not contain business-specific logic.

Good:

```
format_timestamp()

```

Bad:

```
calculate_medical_evaluation_score()

```

---

## Maintain Backward Compatibility

Because multiple services depend on this module:

- Avoid breaking changes
- Document updates
- Add tests

---

# Testing

Shared components require unit tests.

Run:

```bash
pytest
```

---

# Versioning

Changes affecting multiple services should be documented.

Example:

```
feat(shared): add evaluation result type

```

---

# Future Improvements

Planned:

- Shared Python package
- Internal package registry
- Common API contracts
- Shared authentication models

---

# Summary

The Shared Library provides common building blocks that improve consistency, maintainability, and reliability across all AI Evaluation Platform services.
