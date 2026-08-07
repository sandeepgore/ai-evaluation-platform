# ADR-007: Multi-Tenancy Strategy

## Status

Accepted

## Date

2026-08-07

## Context

The AI Evaluation Platform is designed as a SaaS product where multiple organizations use the same platform.

Examples:

- Startup building AI applications
- Enterprise AI teams
- Research organizations
- Internal ML platforms

The platform must support:

- Secure data isolation
- Organization management
- User permissions
- Resource separation
- Enterprise scalability

A multi-tenancy strategy is required.

---

# Decision

We will implement a **shared database, tenant-isolation architecture** initially.

Each customer is represented as an organization.

All tenant-owned resources contain:

```
organization_id
```

Architecture:

```
                 Platform


                    |


        --------------------------------


        Organization A


        Organization B


        Organization C


        --------------------------------


                    |


              Shared Database


```

---

# Tenant Model

Hierarchy:

```
Organization


      |


      Users


      |


      Projects


      |


      Evaluations


      |


      Reports

```

---

# Database Design

Tenant-aware tables:

```
organizations


users


projects


datasets


evaluations


reports

```

Example:

```
projects


----------------------

id

organization_id

name

created_at

```

---

# Data Access Pattern

Every query must include tenant filtering.

Example:

Correct:

```sql
SELECT *

FROM projects

WHERE organization_id = 'tenant_123';

```

Incorrect:

```sql
SELECT *

FROM projects;

```

---

# Tenant Resolution

Tenant identified through:

## JWT Token

Example:

```json
{
  "user_id": "123",
  "organization_id": "company_a"
}
```

---

## Domain Based Routing

Example:

```
company-a.platform.com
```

---

# Authorization Model

Tenant isolation works with RBAC.

Flow:

```
User


 |

Organization


 |

Role


 |

Permission


 |

Resource

```

---

# Resource Isolation

Examples:

Project access:

```
User

 |

Organization Check

 |

Project Ownership Check

 |

Permission Check

 |

Access Granted

```

---

# Background Job Isolation

Workers must maintain tenant context.

Example:

```json
{
  "organization_id": "company_a",
  "project_id": "123",
  "job_id": "456"
}
```

Workers must never process another tenant's data.

---

# Usage Tracking

Track usage per organization:

Metrics:

- API requests
- Tokens consumed
- Evaluations executed
- Storage usage
- Model costs

Example:

```
Organization A


GPT Usage

500000 tokens


Cost

$20

```

---

# Scaling Strategy

## Phase 1

Shared database:

```
100 - 1000 customers


```

---

## Phase 2

Database optimization:

```
Indexes

Partitioning

Read replicas

```

---

## Phase 3

Enterprise isolation:

```
Enterprise Customer


        |


Dedicated Database

```

---

# Security Controls

Implemented:

- Tenant filtering
- Role-based access
- Audit logs
- API authorization
- Data encryption

---

# Alternatives Considered

## Separate Database Per Tenant

Rejected initially.

Reasons:

- Higher operational cost
- Complex migrations
- Difficult management

Future option for enterprise customers.

---

## Separate Schema Per Tenant

Rejected initially.

Reasons:

- Schema management complexity
- Migration overhead

---

## No Tenant Isolation

Rejected.

Reasons:

- Security risk
- Not suitable for SaaS

---

# Consequences

## Benefits

✅ Cost effective  
✅ Easy onboarding  
✅ Simple operations  
✅ Supports SaaS model  
✅ Enterprise migration path

---

## Trade-offs

❌ Requires strict query filtering  
❌ Shared database resource limits  
❌ More careful security design required

---

# Future Considerations

Possible enhancements:

- Database per enterprise tenant
- Tenant-specific encryption keys
- Regional data residency
- Advanced policy engine

---

# Summary

The platform will start with shared database multi-tenancy using organization-based isolation, providing a scalable foundation for a SaaS AI evaluation product.
