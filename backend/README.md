# AI Evaluation Platform

<p align="center">
Enterprise-grade platform for evaluating, benchmarking, and monitoring AI systems.
</p>

---

# Overview

AI Evaluation Platform is an open-source framework designed to help teams measure, validate, and improve Large Language Models (LLMs), RAG systems, and AI applications.

The platform provides:

- Automated AI evaluation
- Model benchmarking
- RAG quality measurement
- Hallucination detection
- AI safety evaluation
- Cost and performance tracking
- Production AI observability

---

# Problem

Modern AI systems require continuous evaluation.

Common challenges:

- LLM responses are unpredictable
- Hallucinations are difficult to detect
- Model selection requires benchmarking
- AI costs increase rapidly
- Quality changes after deployment

This platform provides a unified solution for AI quality management.

---

# Architecture

## Authentication and roles

The API uses bearer access tokens. Configure `AUTH_SECRET_KEY` with a long random value and set `ACCESS_TOKEN_EXPIRE_MINUTES` before deployment. Apply database migrations with `alembic upgrade head` before starting the application.

Create the first account through the frontend registration form; the first registered account becomes the initial administrator, and later registrations receive the `user` role. Administrators can assign `admin`, `dev`, or `user` from **User access** in the app. `user` accounts have read-only API access, `dev` accounts can modify platform resources, and organization changes and user-role management require `admin`.

The frontend stores the bearer token in browser local storage. For production, serve the frontend and API over HTTPS and use a unique signing secret.

Successful and failed write requests, sign-ins, and registrations are recorded in `audit_logs`. Administrators can review the latest events from **Audit log**; role changes include the old and new roles. Request bodies, passwords, and tokens are never stored in audit records.

---

```
                         Users

                           |

                    React Frontend

                           |

                    FastAPI Backend

                           |

        -------------------------------------

        |                 |                 |

 Evaluation Engine   Model Gateway     Workers

        |                 |                 |

        -------------------------------------

                           |

              PostgreSQL + Redis

                           |

                  Object Storage

```

---

# Core Components

## Backend API

Technology:

- FastAPI
- PostgreSQL
- SQLAlchemy

Responsibilities:

- Authentication
- Projects
- Users
- Evaluation orchestration
- APIs

---

## Frontend

Technology:

- React
- TypeScript
- Vite

Responsibilities:

- Dashboard
- Reports
- Analytics
- Configuration

---

## Evaluation Engine

Responsibilities:

- Accuracy evaluation
- Faithfulness scoring
- Hallucination detection
- RAG evaluation
- Safety checks

---

## Model Gateway

Provides unified access to:

- OpenAI
- Gemini
- Anthropic
- Ollama
- Local models

Features:

- Provider abstraction
- Cost tracking
- Routing
- Rate limiting

---

## Worker System

Handles:

- Background evaluations
- Dataset processing
- Report generation
- Scheduled jobs

---

# Technology Stack

| Layer      | Technology             |
| ---------- | ---------------------- |
| Backend    | FastAPI                |
| Frontend   | React + TypeScript     |
| Database   | PostgreSQL             |
| Cache      | Redis                  |
| AI         | OpenAI, Gemini, Ollama |
| Queue      | Redis Workers          |
| Container  | Docker                 |
| Deployment | Kubernetes             |
| Monitoring | Prometheus + Grafana   |

---

# Features

## Evaluation

✅ LLM evaluation  
✅ RAG evaluation  
✅ Benchmarking  
✅ Custom metrics

## Enterprise

✅ Multi-tenancy  
✅ RBAC  
✅ Audit logging  
✅ API access

## Infrastructure

✅ Docker support  
✅ Kubernetes ready  
✅ CI/CD pipelines  
✅ Monitoring support

---

# Repository Structure

```
ai-evaluation-platform

├── backend
├── frontend
├── evaluation-engine
├── model-gateway
├── workers
├── shared
├── infrastructure
├── docs
├── datasets
├── benchmarks
└── scripts

```

---

# Local Development

Clone:

```bash
git clone <repository-url>

cd ai-evaluation-platform

```

Start services:

```bash
docker compose up
```

Backend:

```
http://localhost:8000
```

Frontend:

```
http://localhost:5173
```

---

# Documentation

Complete documentation:

```
docs/

├── architecture
├── ai-evaluation
├── api
├── database
├── deployment
├── development
├── security
└── prd

```

---

# Roadmap

Current:

```
Phase 1

MVP Evaluation Platform

```

Future:

```
Phase 2

Advanced AI Evaluation


Phase 3

Production AI Monitoring


Phase 4

Enterprise SaaS Platform

```

---

# Contributing

Contributions are welcome.

See:

```
docs/development/contribution-guide.md

```

---

# License

MIT License

---

# Vision

Build the standard platform for measuring and improving AI system quality.
