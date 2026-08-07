# ADR-010: Object Storage Architecture

## Status

Accepted

## Date

2026-08-07

## Context

The AI Evaluation Platform generates and manages large amounts of unstructured data.

Examples:

- Evaluation datasets
- Model outputs
- Generated reports
- Prompt templates
- Benchmark files
- Execution logs
- Export files

Relational databases are not suitable for storing large binary objects.

The platform requires scalable storage with:

- High durability
- Large file support
- Low cost
- Easy access
- Version management

---

# Decision

We will use **Object Storage** for large files and unstructured data.

Initial compatible solutions:

- AWS S3
- MinIO (local development)
- Cloud S3-compatible storage

Architecture:

```
                 Platform Services


                       |


                 Object Storage


        --------------------------------


        |              |               |


    Datasets       Reports        Artifacts


        |              |               |


        --------------------------------


                 PostgreSQL


        (Metadata Only)

```

---

# Storage Responsibilities

## Dataset Storage

Stores:

- Training datasets
- Evaluation datasets
- Test cases
- Benchmark files

Example:

```
datasets/


 organization-a/


     project-1/


          dataset-v1.json

          dataset-v2.json

```

---

## Evaluation Reports

Stores:

- HTML reports
- JSON reports
- CSV exports
- Visualization files

Example:

```
reports/


evaluation-123/


     report.html

     metrics.json

```

---

## Model Artifacts

Future support:

- Fine-tuned models
- Embedding files
- Model configurations

Example:

```
models/


customer-model/


    config.json

    weights.bin

```

---

# Database Relationship

PostgreSQL stores metadata:

Example:

```
evaluation_files


-----------------------


id


organization_id


file_name


storage_path


created_at

```

Actual file:

```
Object Storage


evaluation/report.json

```

---

# File Upload Flow

```
User


 |

Upload Dataset


 |

Backend API


 |

Generate Storage URL


 |

Object Storage


 |

Save Metadata


 |

PostgreSQL

```

---

# Access Strategy

## Development

Use:

```
MinIO

+

Docker

```

Benefits:

- Local S3-compatible environment
- No cloud dependency

---

## Production

Use:

```
AWS S3

or

Cloud Compatible Storage

```

---

# Security

Object storage security:

- Private buckets
- Signed URLs
- Encryption at rest
- Access policies
- Tenant isolation

Example:

```
User Request

      |

Permission Check

      |

Generate Signed URL

      |

Temporary Access

```

---

# Versioning

Important files support versions.

Example:

```
Dataset


v1

v2

v3

```

Benefits:

- Reproducible evaluations
- Experiment tracking
- Auditing

---

# Lifecycle Management

Large files require lifecycle rules.

Example:

```
Temporary Reports


30 days


       |

Archive


       |

Delete

```

---

# Alternatives Considered

## PostgreSQL Large Objects

Rejected.

Reasons:

- Database size growth
- Backup complexity
- Poor scalability

---

## Local File Storage

Rejected.

Reasons:

- Not highly available
- Difficult scaling
- Deployment dependency

---

## MongoDB GridFS

Rejected.

Reasons:

- Additional database dependency
- Object storage provides better scalability

---

# Consequences

## Benefits

✅ Unlimited scalability  
✅ Low storage cost  
✅ Better database performance  
✅ Cloud ready  
✅ Supports large AI artifacts

---

## Trade-offs

❌ Additional storage system  
❌ Requires access management  
❌ Network dependency

---

# Future Considerations

Possible improvements:

- Multi-region storage
- Data retention policies
- Compression
- Deduplication
- Content hashing
- Customer-managed storage

---

# Summary

Object storage is selected as the platform storage layer for large files, datasets, reports, and AI artifacts while PostgreSQL remains responsible for structured metadata.
