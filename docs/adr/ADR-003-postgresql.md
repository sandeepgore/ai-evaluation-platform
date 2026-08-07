# ADR-003: PostgreSQL Database

## Status

Accepted

## Date

2026-08-07

## Context

The AI Evaluation Platform requires persistent storage for:

- Organizations
- Users
- Projects
- Models
- Datasets
- Evaluation jobs
- Evaluation results
- Metrics
- Reports
- Audit logs

The database must support:

- Strong consistency
- Complex relationships
- Multi-tenancy
- Analytics queries
- JSON-based AI metadata
- High reliability

---

# Decision

We will use **PostgreSQL** as the primary relational database.

Technology:

```
PostgreSQL

+

SQLAlchemy ORM

+

Alembic Migration

+

pgvector (future)
```

---

# Database Architecture

High-level design:

```
                 Backend API


                     |


              SQLAlchemy ORM


                     |


                PostgreSQL


        ---------------------------

        |            |            |

     Users      Projects     Evaluations


        |            |            |

     Reports    Metrics     Audit Logs

```

---

# Why PostgreSQL

## Relational Data Support

The platform contains highly related entities:

Example:

```
Organization

      |

Project

      |

Evaluation

      |

Metric Results

```

A relational database provides:

- Foreign keys
- Constraints
- Transactions
- Data integrity

---

# JSONB Support

AI systems generate dynamic metadata.

Examples:

- Model parameters
- Prompt configurations
- Evaluation outputs

PostgreSQL JSONB supports:

```json
{
  "model": "gpt",
  "temperature": 0.2,
  "tokens": 1500
}
```

Benefits:

- Flexible schema
- Queryable JSON data
- Hybrid relational/document approach

---

# Multi-Tenancy Support

Initial strategy:

Shared database with tenant isolation.

Every tenant-owned table contains:

```
organization_id
```

Example:

```sql
projects

------------------

id

organization_id

name

created_at

```

Query:

```sql
SELECT *

FROM projects

WHERE organization_id='tenant_id';

```

---

# Indexing Strategy

Important indexes:

## Tenant Queries

```sql
CREATE INDEX idx_projects_org

ON projects(organization_id);
```

---

## Evaluation Search

```sql
CREATE INDEX idx_evaluation_status

ON evaluations(status);
```

---

## Time-Based Queries

```sql
CREATE INDEX idx_created_at

ON evaluations(created_at);
```

---

# Migration Strategy

Database changes are managed using:

```
Alembic

    |

Migration Files

    |

PostgreSQL Schema

```

Example:

```
alembic revision

        |

Create Migration

        |

alembic upgrade

        |

Apply Changes

```

---

# Backup Strategy

Production backups:

- Automated snapshots
- Point-in-time recovery
- Disaster recovery plan

---

# Performance Strategy

Optimization:

- Connection pooling
- Query optimization
- Index management
- Read replicas (future)

---

# AI-Specific Extensions

Future support:

## pgvector

For storing:

- Embeddings
- Semantic search vectors
- Evaluation similarity

Architecture:

```
Dataset

   |

Embedding Generation

   |

pgvector

   |

Similarity Search

```

---

# Alternatives Considered

## MongoDB

Rejected.

Reasons:

- Less suitable for relational workflows
- Complex transactions
- Multi-tenant consistency challenges

---

## MySQL

Rejected.

Reasons:

- PostgreSQL provides stronger JSON support
- Better advanced query capabilities

---

## DynamoDB

Rejected.

Reasons:

- Requires access-pattern-first design
- More complexity for analytics workloads

---

# Consequences

## Benefits

✅ Strong consistency  
✅ Enterprise reliability  
✅ JSON flexibility  
✅ Excellent tooling  
✅ Large ecosystem

---

## Trade-offs

❌ Requires schema management  
❌ Scaling writes requires planning  
❌ More operational responsibility

---

# Future Considerations

Possible improvements:

- Read replicas
- Database partitioning
- Sharding for large tenants
- Dedicated enterprise databases

---

# Summary

PostgreSQL is selected as the core database because it provides the reliability, flexibility, and scalability required for an enterprise AI evaluation SaaS platform.
