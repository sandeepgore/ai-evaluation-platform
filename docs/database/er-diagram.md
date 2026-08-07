# AI Evaluation Platform

# Database ER Diagram

## 1. Entity Relationship Overview

```mermaid
erDiagram


    USER {
        uuid id PK
        string email
        string password_hash
        string first_name
        string last_name
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }


    ORGANIZATION {
        uuid id PK
        string name
        string slug
        string plan
        timestamp created_at
        timestamp updated_at
    }


    ROLE {
        uuid id PK
        string name
        json permissions
    }


    ORGANIZATION_MEMBER {
        uuid id PK
        uuid organization_id FK
        uuid user_id FK
        uuid role_id FK
        timestamp created_at
    }


    PROJECT {
        uuid id PK
        uuid organization_id FK
        string name
        string description
        string status
        uuid created_by FK
        timestamp created_at
        timestamp updated_at
    }


    DATASET {
        uuid id PK
        uuid project_id FK
        string name
        string version
        string storage_path
        timestamp created_at
    }


    DATASET_RECORD {
        uuid id PK
        uuid dataset_id FK
        json input
        json expected_output
        json metadata
    }


    MODEL {
        uuid id PK
        uuid project_id FK
        string provider
        string model_name
        json configuration
        timestamp created_at
    }


    EVALUATION {
        uuid id PK
        uuid project_id FK
        uuid dataset_id FK
        uuid model_id FK
        string status
        timestamp started_at
        timestamp completed_at
    }


    METRIC {
        uuid id PK
        uuid evaluation_id FK
        string metric_name
        float score
        json metadata
    }


    REPORT {
        uuid id PK
        uuid evaluation_id FK
        string type
        string storage_url
        timestamp created_at
    }


    USAGE_RECORD {
        uuid id PK
        uuid organization_id FK
        string provider
        integer input_tokens
        integer output_tokens
        decimal cost
        timestamp created_at
    }


    AUDIT_LOG {
        uuid id PK
        uuid organization_id FK
        uuid user_id FK
        string action
        json metadata
        timestamp created_at
    }



    USER ||--o{ ORGANIZATION_MEMBER : belongs_to

    ORGANIZATION ||--o{ ORGANIZATION_MEMBER : contains

    ROLE ||--o{ ORGANIZATION_MEMBER : assigned


    ORGANIZATION ||--o{ PROJECT : owns


    USER ||--o{ PROJECT : creates


    PROJECT ||--o{ DATASET : contains

    DATASET ||--o{ DATASET_RECORD : contains


    PROJECT ||--o{ MODEL : uses


    PROJECT ||--o{ EVALUATION : runs


    DATASET ||--o{ EVALUATION : evaluated


    MODEL ||--o{ EVALUATION : executes


    EVALUATION ||--o{ METRIC : generates


    EVALUATION ||--o{ REPORT : creates


    ORGANIZATION ||--o{ USAGE_RECORD : consumes


    ORGANIZATION ||--o{ AUDIT_LOG : generates


    USER ||--o{ AUDIT_LOG : performs
```

---

# 2. Relationship Explanation

## User → Organization

A user can belong to multiple organizations.

Example:

```
User A

 |

Organization 1

Organization 2
```

---

## Organization → Projects

An organization owns multiple AI projects.

Example:

```
Company

 |

Customer Support Bot

Medical Assistant

Document AI
```

---

## Project → Dataset

Each project can contain multiple datasets.

Examples:

```
Project

 |

Dataset v1

Dataset v2

Dataset v3
```

---

## Project → Models

A project can evaluate multiple AI models.

Example:

```
Customer Bot Project

 |

GPT Model

Claude Model

Llama Model
```

---

## Evaluation Lifecycle

Relationship:

```
Dataset

   +

Model

   |

Evaluation

   |

Metrics

   |

Report
```

Example:

```
Dataset:
Customer Questions


Model:
GPT


Evaluation:
GPT Accuracy Test


Metrics:
Accuracy = 92%

Report:
PDF
```

---

# 3. Future Database Extensions

## Billing Module

Future tables:

```
Subscription

Invoice

Payment

UsageLimit
```

---

## Enterprise Security

Future tables:

```
SSOConfiguration

SecurityPolicy

ComplianceReport
```

---

## Advanced Evaluation

Future tables:

```
PromptTemplate

Experiment

ExperimentVersion

HumanFeedback
```

---

# 4. Design Notes

## UUID Primary Keys

All entities use UUIDs.

Benefits:

- Distributed systems support
- Better security
- Easier migration

---

## JSONB Usage

JSONB is used for flexible AI metadata.

Examples:

- Model parameters
- Evaluation configuration
- Custom metrics

---

## Soft Delete Strategy

Future support:

```
deleted_at TIMESTAMP
```

Allows:

- Data recovery
- Compliance requirements

---

# Summary

The ER model supports:

- Multi-tenant SaaS architecture
- AI model evaluation workflows
- Dataset versioning
- Metrics tracking
- Enterprise auditing

The schema is designed for future scale and commercial deployment.
