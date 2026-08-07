# ADR-004: Event Driven Worker Architecture

## Status

Accepted

## Date

2026-08-07

## Context

AI evaluations are long-running operations.

Examples:

- Running thousands of test cases
- Calling multiple LLM providers
- Calculating evaluation metrics
- Generating reports
- Processing datasets

These operations should not block the API layer.

The system requires:

- Asynchronous processing
- Job management
- Retry handling
- Horizontal scalability
- Background execution

---

# Decision

We will use an **event-driven worker architecture**.

The system will separate:

- API request handling
- Job execution
- Result processing

Architecture:

```
                Client


                  |


             Backend API


                  |


          Create Evaluation Job


                  |


               Redis Queue


                  |


        -----------------------


        Worker 1   Worker 2   Worker 3


        -----------------------


                  |


          Evaluation Engine


                  |


             PostgreSQL

```

---

# Worker Responsibilities

Workers handle:

- Evaluation execution
- Dataset processing
- Model calls
- Metric calculation
- Report generation

---

# Job Lifecycle

```
Created

   |

Queued

   |

Processing

   |

Completed

   |

Stored

```

Failure:

```
Processing

      |

Error

      |

Retry

      |

Failed

```

---

# Queue Architecture

Redis is used as the message broker.

Example queues:

```
Redis


|

├── evaluation_queue

├── dataset_queue

├── report_queue

└── notification_queue

```

---

# Evaluation Flow

Example:

```
User

 |

Start Evaluation

 |

Backend API

 |

Create Job

 |

Redis Queue

 |

Worker Picks Job

 |

Evaluation Engine

 |

Store Results

 |

Notify User

```

---

# Why Event Driven Architecture

## Non Blocking APIs

Without workers:

```
API Request

      |

Run Evaluation

      |

Wait 30 minutes

```

Problem:

- Timeout
- Poor user experience

With workers:

```
API Request

      |

Queue Job

      |

Return Immediately

```

---

## Scalability

Workers scale independently.

Example:

Low traffic:

```
2 Workers

```

High traffic:

```
50 Workers

```

---

## Reliability

Benefits:

- Retry failed jobs
- Track status
- Resume processing

---

# Worker Technology

Initial implementation:

```
Python Workers

+

Celery / RQ

+

Redis

```

Future:

```
Kubernetes Jobs

+

Event Streaming

```

---

# Retry Strategy

Example:

```
Attempt 1

   |

Failure

   |

Retry after 10 seconds

   |

Attempt 2

   |

Failure

   |

Retry after 1 minute

```

---

# Job Metadata

Each job stores:

```json
{
  "job_id": "123",
  "organization_id": "abc",
  "project_id": "xyz",
  "status": "running",
  "created_at": "2026-08-07"
}
```

---

# Worker Isolation

Every worker validates:

```
Organization Context

+

Project Access

+

Job Permissions

```

---

# Monitoring

Track:

- Queue length
- Processing time
- Failed jobs
- Retry count
- Worker health

Metrics:

```
Evaluation Duration

Jobs Per Minute

Failure Rate

Queue Latency

```

---

# Alternatives Considered

## Synchronous Processing

Rejected.

Reasons:

- API blocking
- Timeout issues
- Poor scalability

---

## Kafka

Not selected initially.

Reasons:

- Higher operational complexity
- More suitable for very high event volumes

Future option:

- Large-scale event streaming

---

## Cloud Functions

Rejected initially.

Reasons:

- Vendor lock-in
- Long-running AI workloads limitations

---

# Consequences

## Benefits

✅ Scalable processing  
✅ Better user experience  
✅ Fault tolerance  
✅ Independent scaling  
✅ Production ready

---

## Trade-offs

❌ Additional infrastructure  
❌ Requires queue monitoring  
❌ More distributed system complexity

---

# Future Considerations

Possible improvements:

- Kafka integration
- Workflow orchestration
- Distributed tracing
- Priority queues
- GPU worker pools

---

# Summary

The AI Evaluation Platform uses an event-driven worker architecture to execute long-running AI evaluation tasks reliably, asynchronously, and at scale.
