# AI Evaluation Platform

# API Error Handling Strategy

## 1. Introduction

This document defines the error handling standards for the AI Evaluation Platform APIs.

The objective is to provide:

- Consistent error responses
- Better debugging experience
- Secure error exposure
- Clear client communication

---

# 2. Error Handling Architecture

Request flow:

```
Client Request

       |

FastAPI Router

       |

Service Layer

       |

Business Validation

       |

Database

       |

Exception Handler

       |

Standard Error Response
```

---

# 3. Error Response Format

All APIs return errors in a common format.

Example:

```json
{
  "success": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project does not exist",
    "details": null
  },
  "request_id": "abc-123"
}
```

---

# 4. Error Object Structure

| Field      | Description                 |
| ---------- | --------------------------- |
| success    | Always false                |
| code       | Machine-readable error code |
| message    | Human-readable message      |
| details    | Additional information      |
| request_id | Debug identifier            |

---

# 5. Error Categories

## Authentication Errors

Examples:

```
INVALID_CREDENTIALS

TOKEN_EXPIRED

TOKEN_INVALID

UNAUTHORIZED
```

HTTP:

```
401 Unauthorized
```

---

## Authorization Errors

Examples:

```
INSUFFICIENT_PERMISSION

ROLE_REQUIRED
```

HTTP:

```
403 Forbidden
```

---

## Validation Errors

Examples:

```
INVALID_INPUT

MISSING_FIELD

INVALID_FORMAT
```

HTTP:

```
422 Unprocessable Entity
```

---

## Resource Errors

Examples:

```
PROJECT_NOT_FOUND

DATASET_NOT_FOUND

MODEL_NOT_FOUND
```

HTTP:

```
404 Not Found
```

---

## Business Logic Errors

Examples:

```
EVALUATION_ALREADY_RUNNING

DATASET_EMPTY

MODEL_UNAVAILABLE
```

HTTP:

```
400 Bad Request
```

---

## System Errors

Examples:

```
DATABASE_ERROR

SERVICE_UNAVAILABLE

INTERNAL_ERROR
```

HTTP:

```
500 Internal Server Error
```

---

# 6. Error Code Convention

Format:

```
RESOURCE_ACTION_REASON
```

Examples:

```
PROJECT_NOT_FOUND

MODEL_INVALID_CONFIGURATION

DATASET_UPLOAD_FAILED
```

---

# 7. FastAPI Exception Architecture

Structure:

```
backend/app/

exceptions/

    base.py

    authentication.py

    validation.py

    business.py

    system.py
```

---

# 8. Custom Exception Example

```python
class ProjectNotFoundException(
    ApplicationException
):

    code = "PROJECT_NOT_FOUND"

    status_code = 404
```

---

# 9. Global Exception Handler

FastAPI example:

```python
@app.exception_handler(
    ApplicationException
)
async def handler(
    request,
    exc
):

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success":False,
            "error":{
                "code":exc.code,
                "message":exc.message
            }
        }
    )
```

---

# 10. Validation Handling

Pydantic validation errors:

Example:

Request:

```json
{
  "name": ""
}
```

Response:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Name cannot be empty"
  }
}
```

---

# 11. Database Error Handling

Database errors should never expose internal details.

Bad:

```json
{
  "error": "duplicate key users_email_key"
}
```

Good:

```json
{
  "code": "EMAIL_ALREADY_EXISTS",
  "message": "Email already registered"
}
```

---

# 12. External Service Errors

External dependencies:

- OpenAI
- Gemini
- Anthropic
- Ollama

Example:

```json
{
  "code": "MODEL_PROVIDER_ERROR",
  "message": "AI provider unavailable"
}
```

---

# 13. Request ID Tracking

Every request receives:

```
X-Request-ID
```

Purpose:

- Debugging
- Distributed tracing
- Support investigation

Flow:

```
Request ID

 |

API Gateway

 |

Services

 |

Logs
```

---

# 14. Logging Rules

Log:

- Error code
- Request ID
- User ID
- Organization ID
- Stack trace

Do not log:

- Passwords
- API keys
- Tokens
- Sensitive data

---

# 15. Monitoring Integration

Errors are tracked through:

- Application logs
- Prometheus metrics
- Grafana dashboards

Track:

```
error_rate

5xx_count

failed_evaluations

provider_failures
```

---

# 16. Client Retry Strategy

Retry allowed:

```
503 Service unavailable

429 Rate limit
```

Do not retry:

```
400 Bad request

401 Unauthorized

403 Forbidden
```

---

# 17. Error Handling Best Practices

Rules:

- Never expose internal exceptions
- Always return standard format
- Use meaningful error codes
- Log with request IDs
- Monitor production errors

---

# Summary

The error handling architecture provides:

- Predictable API behavior
- Better developer experience
- Secure production operations
- Enterprise-grade debugging capability
