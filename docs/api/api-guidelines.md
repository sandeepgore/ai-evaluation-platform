# AI Evaluation Platform

# API Guidelines

## 1. Introduction

This document defines API development standards for the AI Evaluation Platform.

The API follows:

- REST architecture
- JSON communication
- HTTP standards
- Versioned endpoints

Backend framework:

```
FastAPI
```

Base URL:

```
/api/v1
```

---

# 2. API Design Principles

The API should be:

- Predictable
- Consistent
- Secure
- Easy to consume
- Backward compatible

---

# 3. API Structure

General format:

```
https://domain.com/api/v1/resource
```

Examples:

```
GET    /api/v1/projects

POST   /api/v1/projects

GET    /api/v1/projects/{id}

PUT    /api/v1/projects/{id}

DELETE /api/v1/projects/{id}
```

---

# 4. HTTP Methods

## GET

Used for retrieving resources.

Example:

```
GET /api/v1/projects
```

---

## POST

Used for creating resources.

Example:

```
POST /api/v1/evaluations
```

---

## PUT

Used for complete updates.

Example:

```
PUT /api/v1/projects/{id}
```

---

## PATCH

Used for partial updates.

Example:

```
PATCH /api/v1/projects/{id}
```

---

## DELETE

Used for deleting resources.

Example:

```
DELETE /api/v1/datasets/{id}
```

---

# 5. Resource Naming

Use plural nouns.

Correct:

```
/projects

/datasets

/evaluations

/models
```

Avoid:

```
/createProject

/getDataset
```

---

# 6. Request Format

All requests use JSON.

Example:

```json
{
  "name": "Customer Support Bot",
  "description": "RAG evaluation project"
}
```

---

# 7. Response Format

Successful response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Project"
  },
  "message": "Project created successfully"
}
```

---

# 8. Error Response Format

All errors follow a standard structure.

Example:

```json
{
  "success": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project does not exist"
  }
}
```

---

# 9. HTTP Status Codes

## Success

| Code | Usage              |
| ---- | ------------------ |
| 200  | Successful request |
| 201  | Resource created   |
| 204  | No content         |

---

## Client Errors

| Code | Usage            |
| ---- | ---------------- |
| 400  | Bad request      |
| 401  | Unauthorized     |
| 403  | Forbidden        |
| 404  | Not found        |
| 422  | Validation error |

---

## Server Errors

| Code | Usage               |
| ---- | ------------------- |
| 500  | Internal error      |
| 503  | Service unavailable |

---

# 10. Pagination

Large collections must support pagination.

Example:

```
GET /api/v1/evaluations?page=1&limit=20
```

Response:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 250
  }
}
```

---

# 11. Filtering

Resources support filtering.

Example:

```
GET /api/v1/evaluations?status=completed
```

Examples:

```
?status=running

?model=gpt

?created_after=date
```

---

# 12. Sorting

Use:

```
sort_by
sort_order
```

Example:

```
GET /api/v1/projects?sort_by=created_at&sort_order=desc
```

---

# 13. Search

Search parameter:

```
?q=value
```

Example:

```
GET /api/v1/projects?q=medical
```

---

# 14. Authentication Headers

Protected APIs require:

```
Authorization: Bearer <token>
```

Example:

```
Authorization: Bearer eyJhbGc...
```

---

# 15. API Validation

Validation happens at:

```
Request

 |

Pydantic Schema

 |

Business Logic

 |

Database
```

Example:

```python
class ProjectCreate(BaseModel):

    name: str

    description: str
```

---

# 16. Idempotency

Important operations support idempotency.

Header:

```
Idempotency-Key
```

Used for:

- Evaluation execution
- Report generation
- Dataset upload

---

# 17. API Rate Limiting

Limits apply to:

- Authentication APIs
- Model execution APIs
- Export APIs

Example:

```
100 requests/minute/user
```

---

# 18. Versioning Strategy

Current version:

```
v1
```

Example:

```
/api/v1/projects
```

Future:

```
/api/v2/projects
```

Breaking changes require new versions.

---

# 19. Documentation

API documentation generated using:

```
OpenAPI / Swagger
```

Available at:

```
/docs
```

---

# 20. API Security Rules

Required:

- Authentication
- Authorization
- Input validation
- Rate limiting
- Logging

Never expose:

- Password hashes
- Internal IDs unnecessarily
- API keys

---

# Summary

These API guidelines ensure:

- Consistent REST APIs
- Developer-friendly integration
- Enterprise security
- Future API evolution
