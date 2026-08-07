# ADR-009: Redis Architecture

## Status

Accepted

## Date

2026-08-07

## Context

The AI Evaluation Platform requires fast temporary storage and asynchronous communication.

The platform needs capabilities for:

- Background job queues
- API response caching
- Rate limiting
- Session management
- Real-time status tracking
- Distributed locks

A high-performance in-memory data store is required.

---

# Decision

We will use **Redis** as the primary in-memory data platform.

Redis will be used for:

- Job queues
- Cache layer
- Rate limiting
- Temporary state management
- Worker coordination

Architecture:

```
                    Backend API


                         |


                       Redis


        --------------------------------


        |              |               |


      Queue          Cache        Rate Limit


        |              |               |


     Workers       API Data       Security


```

---

# Redis Responsibilities

## 1. Job Queue Management

Long-running tasks are pushed into Redis queues.

Example:

```
Evaluation Request


        |


Redis Queue


        |


Worker Processing

```

Queues:

```
redis


├── evaluation_queue

├── dataset_queue

├── report_queue

└── notification_queue

```

---

# 2. Caching Layer

Redis improves response performance.

Examples:

## Model Configuration Cache

Without Redis:

```
API

 |

Database Query

 |

Response

```

With Redis:

```
API

 |

Redis Cache

 |

Response

```

---

# 3. Rate Limiting

Protect APIs from excessive usage.

Example:

```
Organization


1000 requests/minute


```

Redis stores:

```
{
 "tenant":"company_a",
 "requests":450,
 "window":"1 minute"
}

```

---

# 4. Real-Time Evaluation Status

Evaluation progress can be stored temporarily.

Example:

```json
{
  "job_id": "123",
  "status": "processing",
  "progress": "65%"
}
```

Frontend can receive updates through:

- Polling
- WebSocket
- Server Sent Events

---

# 5. Distributed Locking

Prevents duplicate processing.

Example:

Problem:

```
Worker A

starts evaluation


Worker B

starts same evaluation

```

Redis lock:

```
Acquire Lock

      |

Process Job

      |

Release Lock

```

---

# Data Expiration Strategy

Temporary data uses TTL.

Example:

```
Cache Entry


Created


 |

TTL 30 minutes


 |

Automatic Removal

```

---

# Queue Architecture

Worker communication:

```
Backend API


     |

Create Job


     |

Redis Queue


     |

Worker


     |

Evaluation Engine


     |

PostgreSQL

```

---

# Redis Deployment

Development:

```
Docker Redis Container

```

Production:

```
Redis Cluster

+

High Availability

+

Persistence

```

---

# Monitoring

Track:

- Memory usage
- Queue size
- Cache hit rate
- Command latency
- Failed jobs

Metrics:

```
redis_memory_usage

queue_length

cache_hit_ratio

command_latency

```

---

# Security

Redis security:

- Authentication enabled
- Private network access
- Encryption in transit
- Access restrictions

---

# Alternatives Considered

## RabbitMQ

Rejected initially.

Reasons:

- Additional infrastructure
- Redis already supports required queue workloads

Future option for complex messaging.

---

## Kafka

Rejected initially.

Reasons:

- Designed for high-volume event streaming
- Operational complexity

---

## Database Queue

Rejected.

Reasons:

- Poor performance
- Database contention

---

# Consequences

## Benefits

✅ Very fast operations  
✅ Simple architecture  
✅ Supports queues and caching  
✅ Reduces database load  
✅ Easy local development

---

## Trade-offs

❌ Requires memory management  
❌ Additional infrastructure  
❌ Persistence configuration required

---

# Future Considerations

Possible improvements:

- Redis Cluster
- Redis Streams
- Advanced workflow queues
- Priority queues
- Event streaming integration

---

# Summary

Redis is selected as the platform's in-memory infrastructure layer, providing caching, asynchronous processing, rate limiting, and real-time capabilities.
