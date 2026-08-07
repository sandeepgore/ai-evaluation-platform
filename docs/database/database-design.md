# AI Evaluation Platform

# Database Design

## 1. Introduction

This document describes the database architecture of the AI Evaluation Platform.

The database is designed to support:

- Multi-tenant organizations
- AI evaluation workflows
- Model management
- Dataset management
- Usage tracking
- Reporting
- Enterprise security

Technology:

- PostgreSQL
- SQLAlchemy ORM
- Alembic migrations

---

# 2. Database Design Principles

## Multi-Tenancy First

Every business entity belongs to an organization.

Example:

```
Organization

      |

 Projects

      |

 Evaluations
```

---

## Data Ownership

Each table should have:

- Primary key
- Created timestamp
- Updated timestamp
- Organization reference (where required)

---

## Auditability

Important actions are tracked through:

- Audit logs
- User activity
- Evaluation history

---

# 3. High Level Entity Relationship

```text
User

 |

Organization Member

 |

Organization

 |

-------------------------

|                       |

Projects              Roles


 |

 |

Dataset

 |

Evaluation

 |

Metrics

 |

Reports
```

---

# 4. Core Tables

# Users Table

Purpose:

Stores platform users.

Columns:

| Column        | Type      | Description        |
| ------------- | --------- | ------------------ |
| id            | UUID      | Primary key        |
| email         | VARCHAR   | User email         |
| password_hash | VARCHAR   | Encrypted password |
| first_name    | VARCHAR   | First name         |
| last_name     | VARCHAR   | Last name          |
| is_active     | BOOLEAN   | Account status     |
| created_at    | TIMESTAMP | Creation time      |
| updated_at    | TIMESTAMP | Update time        |

---

# Organizations Table

Purpose:

Represents tenant accounts.

Columns:

| Column     | Type      |
| ---------- | --------- |
| id         | UUID      |
| name       | VARCHAR   |
| slug       | VARCHAR   |
| plan       | VARCHAR   |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

Example:

```
Acme AI Labs

|

Organization ID: 001
```

---

# Organization Members

Purpose:

Maps users to organizations.

Columns:

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| organization_id | UUID      |
| user_id         | UUID      |
| role_id         | UUID      |
| created_at      | TIMESTAMP |

Relationship:

```
User

 |

Organization Member

 |

Organization
```

---

# Roles Table

Purpose:

RBAC management.

Columns:

| Column      | Type    |
| ----------- | ------- |
| id          | UUID    |
| name        | VARCHAR |
| permissions | JSONB   |

Examples:

```
ADMIN

DEVELOPER

VIEWER
```

---

# 5. Project Management

# Projects Table

Purpose:

Represents AI applications being evaluated.

Columns:

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| organization_id | UUID      |
| name            | VARCHAR   |
| description     | TEXT      |
| status          | VARCHAR   |
| created_by      | UUID      |
| created_at      | TIMESTAMP |

Example:

```
Customer Support Chatbot

Medical RAG Assistant

Document Analyzer
```

---

# 6. Dataset Management

# Datasets Table

Purpose:

Stores evaluation datasets.

Columns:

| Column       | Type      |
| ------------ | --------- |
| id           | UUID      |
| project_id   | UUID      |
| name         | VARCHAR   |
| description  | TEXT      |
| version      | VARCHAR   |
| storage_path | TEXT      |
| created_at   | TIMESTAMP |

---

# Dataset Records

Purpose:

Individual evaluation examples.

Columns:

| Column          | Type  |
| --------------- | ----- |
| id              | UUID  |
| dataset_id      | UUID  |
| input           | JSONB |
| expected_output | JSONB |
| metadata        | JSONB |

Example:

```json
{
  "question": "What is AI?",
  "answer": "Artificial Intelligence"
}
```

---

# 7. Model Management

# Models Table

Purpose:

Stores AI model configurations.

Columns:

| Column        | Type      |
| ------------- | --------- |
| id            | UUID      |
| project_id    | UUID      |
| provider      | VARCHAR   |
| model_name    | VARCHAR   |
| configuration | JSONB     |
| created_at    | TIMESTAMP |

Examples:

```
OpenAI GPT-5

Gemini

Claude

Llama
```

---

# 8. Evaluation Management

# Evaluations Table

Purpose:

Tracks evaluation execution.

Columns:

| Column       | Type      |
| ------------ | --------- |
| id           | UUID      |
| project_id   | UUID      |
| dataset_id   | UUID      |
| model_id     | UUID      |
| status       | VARCHAR   |
| started_at   | TIMESTAMP |
| completed_at | TIMESTAMP |

Statuses:

```
CREATED

RUNNING

COMPLETED

FAILED
```

---

# 9. Evaluation Results

# Metrics Table

Purpose:

Stores evaluation scores.

Columns:

| Column        | Type    |
| ------------- | ------- |
| id            | UUID    |
| evaluation_id | UUID    |
| metric_name   | VARCHAR |
| score         | FLOAT   |
| metadata      | JSONB   |

Examples:

```
Accuracy: 0.92

Faithfulness: 0.87

Safety: 0.98
```

---

# 10. Reports

# Reports Table

Purpose:

Stores generated reports.

Columns:

| Column        | Type      |
| ------------- | --------- |
| id            | UUID      |
| evaluation_id | UUID      |
| type          | VARCHAR   |
| storage_url   | TEXT      |
| created_at    | TIMESTAMP |

Examples:

```
PDF Report

CSV Export

Dashboard Report
```

---

# 11. API Usage Tracking

# Usage Records

Purpose:

Track AI consumption.

Columns:

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| organization_id | UUID      |
| provider        | VARCHAR   |
| input_tokens    | INTEGER   |
| output_tokens   | INTEGER   |
| cost            | DECIMAL   |
| created_at      | TIMESTAMP |

Used for:

- Billing
- Cost analysis
- Optimization

---

# 12. Audit Logs

Purpose:

Track important actions.

Columns:

| Column          | Type      |
| --------------- | --------- |
| id              | UUID      |
| organization_id | UUID      |
| user_id         | UUID      |
| action          | VARCHAR   |
| metadata        | JSONB     |
| created_at      | TIMESTAMP |

Examples:

```
CREATE_PROJECT

DELETE_DATASET

RUN_EVALUATION
```

---

# 13. Database Indexing Strategy

Important indexes:

## Users

```
email
```

## Organizations

```
slug
```

## Projects

```
organization_id
```

## Evaluations

```
project_id

status

created_at
```

## Metrics

```
evaluation_id
```

---

# 14. Data Retention Strategy

Future enterprise features:

- Configurable retention policies
- Dataset archival
- Evaluation history management

---

# 15. Migration Strategy

Database changes are managed using:

```
Alembic Migration


Developer Change

        |

Migration File

        |

Database Upgrade
```

---

# Summary

The database architecture provides:

- SaaS multi-tenancy
- Enterprise security
- AI evaluation tracking
- Cost management
- Future billing support

The schema is designed to evolve from an open-source platform into a commercial AI evaluation product.
