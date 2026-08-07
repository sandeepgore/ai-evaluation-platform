# AI Evaluation Platform

# Data Models

## 1. Introduction

This document defines the application data models used by the backend.

The models are implemented using:

- Python
- SQLAlchemy ORM
- PostgreSQL

Model location:

```
backend/app/models/
```

---

# 2. Base Model

All database models inherit common fields.

Example:

```python
BaseModel

    id: UUID

    created_at: datetime

    updated_at: datetime
```

Common fields:

| Field      | Purpose               |
| ---------- | --------------------- |
| id         | Unique identifier     |
| created_at | Creation timestamp    |
| updated_at | Last update timestamp |

---

# 3. User Model

Purpose:

Represents platform users.

Entity:

```
User
```

Fields:

| Field         | Type     |
| ------------- | -------- |
| id            | UUID     |
| email         | String   |
| password_hash | String   |
| first_name    | String   |
| last_name     | String   |
| is_active     | Boolean  |
| created_at    | DateTime |
| updated_at    | DateTime |

Relationships:

```
User

 |

OrganizationMember

 |

Organization
```

---

# 4. Organization Model

Purpose:

Represents a tenant.

Fields:

| Field      | Type     |
| ---------- | -------- |
| id         | UUID     |
| name       | String   |
| slug       | String   |
| plan       | String   |
| created_at | DateTime |
| updated_at | DateTime |

Relationships:

```
Organization

 |

Projects

 |

Members
```

---

# 5. Role Model

Purpose:

RBAC permissions.

Fields:

| Field       | Type   |
| ----------- | ------ |
| id          | UUID   |
| name        | String |
| permissions | JSONB  |

Example:

```json
{
  "project:create": true,
  "evaluation:run": true
}
```

---

# 6. Organization Member Model

Purpose:

Connect users with organizations.

Fields:

| Field           | Type |
| --------------- | ---- |
| id              | UUID |
| organization_id | UUID |
| user_id         | UUID |
| role_id         | UUID |

Relationships:

```
User

   |

Member

   |

Organization
```

---

# 7. Project Model

Purpose:

Represents an AI application.

Fields:

| Field           | Type   |
| --------------- | ------ |
| id              | UUID   |
| organization_id | UUID   |
| name            | String |
| description     | Text   |
| status          | String |
| created_by      | UUID   |

Relationships:

```
Project

 |

Dataset

 |

Model

 |

Evaluation
```

---

# 8. Dataset Model

Purpose:

Stores evaluation datasets.

Fields:

| Field        | Type   |
| ------------ | ------ |
| id           | UUID   |
| project_id   | UUID   |
| name         | String |
| version      | String |
| storage_path | String |

Relationships:

```
Dataset

 |

DatasetRecord
```

---

# 9. Dataset Record Model

Purpose:

Individual evaluation examples.

Fields:

| Field           | Type  |
| --------------- | ----- |
| id              | UUID  |
| dataset_id      | UUID  |
| input           | JSONB |
| expected_output | JSONB |
| metadata        | JSONB |

Example:

```json
{
  "question": "Explain AI",
  "expected": "Artificial Intelligence"
}
```

---

# 10. Model Configuration Model

Purpose:

Stores AI model details.

Fields:

| Field         | Type   |
| ------------- | ------ |
| id            | UUID   |
| project_id    | UUID   |
| provider      | String |
| model_name    | String |
| configuration | JSONB  |

Example:

```json
{
  "temperature": 0.2,
  "max_tokens": 1000
}
```

---

# 11. Evaluation Model

Purpose:

Represents one evaluation execution.

Fields:

| Field        | Type     |
| ------------ | -------- |
| id           | UUID     |
| project_id   | UUID     |
| dataset_id   | UUID     |
| model_id     | UUID     |
| status       | String   |
| started_at   | DateTime |
| completed_at | DateTime |

Statuses:

```
CREATED

RUNNING

COMPLETED

FAILED
```

---

# 12. Metric Model

Purpose:

Stores evaluation scores.

Fields:

| Field         | Type   |
| ------------- | ------ |
| id            | UUID   |
| evaluation_id | UUID   |
| metric_name   | String |
| score         | Float  |
| metadata      | JSONB  |

Examples:

```
accuracy = 0.91

faithfulness = 0.88
```

---

# 13. Report Model

Purpose:

Stores generated reports.

Fields:

| Field         | Type   |
| ------------- | ------ |
| id            | UUID   |
| evaluation_id | UUID   |
| type          | String |
| storage_url   | String |

Report types:

```
PDF

CSV

JSON
```

---

# 14. Usage Record Model

Purpose:

Tracks AI consumption.

Fields:

| Field           | Type    |
| --------------- | ------- |
| id              | UUID    |
| organization_id | UUID    |
| provider        | String  |
| input_tokens    | Integer |
| output_tokens   | Integer |
| cost            | Decimal |

Used for:

- Billing
- Analytics
- Cost optimization

---

# 15. Audit Log Model

Purpose:

Tracks system activities.

Fields:

| Field           | Type   |
| --------------- | ------ |
| id              | UUID   |
| organization_id | UUID   |
| user_id         | UUID   |
| action          | String |
| metadata        | JSONB  |

Examples:

```
USER_LOGIN

PROJECT_CREATED

EVALUATION_STARTED
```

---

# 16. Model Relationships Summary

```
User

 |

OrganizationMember

 |

Organization

 |

Project

 |

---------------------------------

|              |                |

Dataset       Model        Evaluation

 |

DatasetRecord

                      |

                   Metrics

                      |

                   Reports
```

---

# 17. Implementation Guidelines

## Naming Convention

Database:

```
snake_case
```

Python:

```
PascalCase classes

snake_case fields
```

Example:

Database:

```
created_at
```

Python:

```python
created_at: datetime
```

---

## Relationship Loading

Default:

- Lazy loading

For heavy queries:

- Explicit joins
- Select loading

---

## Validation

Database validation:

- Foreign keys
- Constraints
- Indexes

Application validation:

- Pydantic schemas
- Business rules

---

# Summary

These models define the foundation for implementing the backend database layer.

They support:

- Multi-tenancy
- AI evaluation workflows
- Model management
- Reporting
- Enterprise expansion
