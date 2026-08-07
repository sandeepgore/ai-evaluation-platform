# Coding Standards

## Overview

This document defines coding standards and engineering practices for the AI Evaluation Platform.

The goal is to maintain:

- Clean code
- Consistent architecture
- Easy collaboration
- Production quality
- Long-term maintainability

---

# General Principles

All code should follow:

## SOLID Principles

- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

## Clean Architecture

Separate:

```
Controller

    |

Service

    |

Repository

    |

Database

```

Business logic should not depend directly on infrastructure.

---

# Python Backend Standards

## Version

Use:

```
Python 3.12+

```

---

# Formatting

Use:

```
ruff format

```

Example:

```python
def calculate_score(value: float) -> float:
    return value * 100
```

---

# Type Hints

All public functions require type hints.

Good:

```python
def evaluate_model(
    model_name: str,
    dataset_id: str
) -> EvaluationResult:
    pass
```

Avoid:

```python
def evaluate_model(model, dataset):
    pass
```

---

# Naming Convention

## Files

Use snake_case:

```
evaluation_service.py

model_provider.py

```

## Classes

Use PascalCase:

```python
class EvaluationEngine:
    pass
```

## Functions

Use snake_case:

```python
def calculate_metrics():
    pass
```

## Constants

Use uppercase:

```python
MAX_RETRY_COUNT = 3
```

---

# FastAPI Standards

## API Structure

```
api/

 v1/

   evaluations.py

   models.py

   projects.py

```

---

# Endpoint Naming

Use REST conventions.

Good:

```
GET /projects

POST /evaluations

GET /evaluations/{id}

DELETE /models/{id}

```

Avoid:

```
/getProjects

/createEvaluation

```

---

# Pydantic Schemas

Separate request and response models.

Example:

```python
class EvaluationCreate(BaseModel):
    model_id: str
    dataset_id: str


class EvaluationResponse(BaseModel):
    id: str
    status: str
```

---

# Database Standards

## Naming

Tables:

```
snake_case

```

Example:

```
evaluation_results

model_configs

```

Columns:

```
created_at

updated_at

organization_id

```

---

# Repository Pattern

Database access should happen through repositories.

Example:

```
Service

 |

Repository

 |

Database

```

Avoid database queries directly inside API routes.

---

# React + TypeScript Standards

## Components

Use PascalCase.

Example:

```
EvaluationDashboard.tsx

```

---

# Hooks

Prefix with:

```
use

```

Example:

```typescript
useEvaluationData();
```

---

# State Management

Keep state separated:

```
store/

features/

services/

```

---

# Type Safety

Avoid:

```typescript
any;
```

Prefer:

```typescript
interface Evaluation {
  id: string;
  score: number;
}
```

---

# AI Evaluation Code Standards

## Evaluators

Every evaluator must:

- Have clear input/output
- Be independently testable
- Provide explanation
- Return confidence score

Example:

```python
{
 "score":0.92,
 "reason":"Answer matches context",
 "confidence":0.95
}
```

---

# Model Provider Standards

All providers must implement common interface.

Example:

```
BaseProvider


     |

----------------


OpenAIProvider


GeminiProvider


OllamaProvider

```

---

# Error Handling

Use structured errors.

Example:

```json
{
  "error_code": "MODEL_TIMEOUT",
  "message": "Provider timeout"
}
```

Avoid:

```python
raise Exception("failed")
```

---

# Logging Standards

Use structured logging.

Example:

```python
logger.info(
    "evaluation_completed",
    extra={
        "evaluation_id":id
    }
)
```

Never log:

- API keys
- Passwords
- Personal information

---

# Testing Standards

Every feature should include:

- Unit tests
- Integration tests
- API tests

Example:

```
feature

 |

implementation

 |

tests

```

---

# Documentation Standards

Every major feature requires:

- README update
- API documentation
- Architecture decision if required

---

# Code Review Checklist

Before merging:

✅ Tests passing  
✅ No secrets committed  
✅ Documentation updated  
✅ Type checks passing  
✅ Linting passing  
✅ Security reviewed

---

# Summary

Following these coding standards ensures the AI Evaluation Platform remains scalable, secure, and maintainable as it grows into an enterprise-grade product.
