# AI Evaluation Platform

# Docker Architecture

## 1. Introduction

This document defines the Docker architecture used for local development and containerized deployments.

Docker provides:

- Consistent environments
- Service isolation
- Easy onboarding
- Reproducible deployments

---

# 2. Container Architecture

The platform runs as multiple containers:

```
                    User

                     |

                Frontend Container

                     |

              Backend API Container

                     |

 ------------------------------------------------

 |                    |                         |

Evaluation Engine   Model Gateway          Worker

 |

 |

PostgreSQL Container

 |

Redis Container

```

---

# 3. Docker Services

## Frontend

Technology:

```
React + TypeScript + Vite
```

Container:

```
frontend
```

Responsibilities:

- User interface
- Dashboard
- Evaluation visualization

Port:

```
5173
```

---

# Backend API

Technology:

```
FastAPI
```

Container:

```
backend
```

Responsibilities:

- Authentication
- Project management
- API endpoints
- Business logic

Port:

```
8000
```

---

# Evaluation Engine

Container:

```
evaluation-engine
```

Responsibilities:

- Run evaluations
- Calculate metrics
- Generate scores

Examples:

```
Accuracy

Faithfulness

Relevance

Safety
```

---

# Model Gateway

Container:

```
model-gateway
```

Responsibilities:

- AI provider abstraction
- Model routing
- Cost tracking

Supported providers:

```
OpenAI

Gemini

Anthropic

Ollama
```

---

# Workers

Container:

```
workers
```

Responsibilities:

- Background processing
- Queue execution
- Scheduled jobs

Examples:

```
Dataset processing

Evaluation execution

Report generation
```

---

# PostgreSQL

Container:

```
postgres
```

Purpose:

- Application data
- Users
- Projects
- Evaluations
- Reports

Port:

```
5432
```

---

# Redis

Container:

```
redis
```

Purpose:

- Cache
- Message queue
- Job coordination

Port:

```
6379
```

---

# 4. Docker Compose Architecture

File:

```
docker-compose.yml
```

Example structure:

```yaml
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"

  postgres:
    image: postgres

  redis:
    image: redis
```

---

# 5. Network Architecture

All services communicate through:

```
Docker Network

        |

ai-evaluation-network
```

Example:

Backend:

```
postgres:5432
```

Redis:

```
redis:6379
```

---

# 6. Volume Management

Persistent data:

## PostgreSQL

```
postgres-data
```

Purpose:

- Database persistence

---

## Redis

```
redis-data
```

Purpose:

- Queue persistence

---

# 7. Environment Configuration

Environment variables:

```
.env
```

Example:

```
DATABASE_URL

REDIS_URL

JWT_SECRET

OPENAI_API_KEY

GEMINI_API_KEY
```

Never commit:

```
.env
```

---

# 8. Development Commands

Start:

```bash
docker compose up
```

Background:

```bash
docker compose up -d
```

Stop:

```bash
docker compose down
```

Rebuild:

```bash
docker compose build
```

---

# 9. Logs

All services:

```bash
docker compose logs
```

Backend:

```bash
docker compose logs backend
```

Follow logs:

```bash
docker compose logs -f backend
```

---

# 10. Health Checks

Each service should expose health status.

Example:

Backend:

```
GET /health
```

Response:

```json
{
  "status": "healthy"
}
```

---

# 11. Security Practices

Containers should:

- Run as non-root user
- Use minimal images
- Avoid secrets inside images
- Keep dependencies updated

---

# 12. Production Considerations

Docker is used for:

Development:

```
Docker Compose
```

Production:

```
Kubernetes
```

Production improvements:

- Container registry
- Image scanning
- Auto scaling
- Rolling deployments

---

# 13. CI/CD Integration

Pipeline:

```
Code Commit

      |

Build Docker Image

      |

Security Scan

      |

Push Registry

      |

Deploy
```

---

# Summary

Docker architecture provides:

- Service isolation
- Reproducible environments
- Easy scaling path
- Production readiness

The architecture can evolve from Docker Compose to Kubernetes without major redesign.
