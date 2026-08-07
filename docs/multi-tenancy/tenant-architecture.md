# AI Evaluation Platform

# Multi-Tenant Architecture

## 1. Introduction

This document defines the multi-tenant architecture of the AI Evaluation Platform.

The platform is designed as a SaaS product where multiple organizations can use the same application while keeping their data isolated and secure.

Goals:

- Secure tenant isolation
- Scalable SaaS architecture
- Enterprise-ready deployment
- Flexible resource management

---

# 2. Multi-Tenant Concept

A tenant represents an organization using the platform.

Example:

```
AI Evaluation Platform


        |

--------------------------------

|                              |

Company A                 Company B


Tenant A                  Tenant B


Projects                  Projects

Users                     Users

Evaluations               Evaluations

--------------------------------
```

---

# 3. Tenant Hierarchy

Architecture:

```
Platform

    |

Organization (Tenant)

    |

Users

    |

Projects

    |

Datasets

    |

Evaluations

    |

Reports
```

---

# 4. Core Entities

## Organization

Represents a customer.

Example:

```
organization

----------------

id

name

plan

created_at
```

---

## User

Belongs to an organization.

Example:

```
user

----------------

id

organization_id

email

role
```

---

## Project

Owned by organization.

Example:

```
project

----------------

id

organization_id

name
```

---

## Evaluation

Belongs to project.

Example:

```
evaluation

----------------

id

organization_id

project_id

status
```

---

# 5. Tenant Isolation Strategy

The platform uses:

```
Shared Application

        +

Tenant Data Isolation
```

Every tenant-owned table contains:

```
organization_id
```

Example:

```
projects


id

organization_id

name

created_at
```

---

# 6. Data Access Flow

Request:

```
User Request

        |

Authentication

        |

Extract Organization ID

        |

Permission Check

        |

Database Query


WHERE organization_id = current_user.organization_id

        |

Return Data
```

---

# 7. Database Design

Initial SaaS approach:

## Shared Database

```
PostgreSQL


Tenant A Data

Tenant B Data

Tenant C Data
```

Separated using:

```
organization_id
```

Advantages:

- Lower cost
- Easy scaling
- Simple operations

---

# 8. Enterprise Isolation Options

For enterprise customers:

## Schema Isolation

Example:

```
database

 |

tenant_company_a_schema

 |

tenant_company_b_schema
```

---

## Database Isolation

Dedicated database:

```
Customer A

 |

Database A


Customer B

 |

Database B
```

Benefits:

- Strong isolation
- Compliance support

---

# 9. Tenant Resolution

Tenant identified using:

## JWT Token

Example:

```json
{
  "user_id": "123",
  "organization_id": "company_001"
}
```

---

## Request Header

Example:

```
X-Organization-ID
```

---

## Domain Based

Example:

```
company.platform.com
```

---

# 10. Authorization Model

Access:

```
Tenant

 |

Role

 |

Permission

 |

Resource
```

Example:

```
Company Admin

can manage

Company Projects
```

---

# 11. Resource Isolation

Every query must include tenant filtering.

Correct:

```sql
SELECT *

FROM projects

WHERE organization_id='tenant1';
```

Incorrect:

```sql
SELECT *

FROM projects;
```

---

# 12. Background Worker Isolation

Workers must maintain tenant context.

Example:

```
Evaluation Job


{

tenant_id:"company_a",

project_id:"123"

}
```

Worker:

```
Process Job

        |

Load Tenant Context

        |

Execute Evaluation

        |

Store Result
```

---

# 13. AI Model Usage Isolation

Track usage per tenant.

Example:

```
Tenant A

|

OpenAI Tokens

|

Cost


Tenant B

|

Gemini Tokens

|

Cost
```

Required metrics:

- Token usage
- API cost
- Evaluation count
- Storage usage

---

# 14. Tenant Resource Limits

Control:

## Evaluation Limits

Example:

```
Free Plan:

100 evaluations/month
```

---

## API Limits

Example:

```
1000 requests/hour
```

---

## Storage Limits

Example:

```
10 GB datasets
```

---

# 15. Tenant Security Controls

Implemented:

- Tenant validation
- Permission checks
- Audit logging
- Data filtering
- API isolation

---

# 16. SaaS Subscription Model

Future:

```
Free

 |

Professional

 |

Enterprise
```

Features controlled by:

```
Subscription Plan

        |

Feature Flags

        |

Access Control
```

---

# 17. Scaling Strategy

Growth:

```
100 Tenants

        |

Shared Database


10,000 Tenants

        |

Database Optimization


Enterprise Customers

        |

Dedicated Infrastructure
```

---

# 18. Compliance Considerations

Enterprise requirements:

- Data isolation
- Audit logs
- Data retention policies
- Access reviews

---

# Summary

The multi-tenant architecture enables:

- SaaS deployment
- Enterprise customers
- Secure data isolation
- Future scaling

Design principle:

```
One Platform

Multiple Organizations

Complete Data Isolation
```
