# AI Evaluation Platform

# Local Development Guide

## 1. Introduction

This document explains how to set up and run the AI Evaluation Platform locally.

The local environment includes:

- Backend API
- Frontend application
- Evaluation Engine
- Model Gateway
- Worker services
- PostgreSQL
- Redis

Architecture:

```
Developer Machine

        |

Docker Compose

        |

--------------------------------

Backend

Frontend

Evaluation Engine

Workers

PostgreSQL

Redis

--------------------------------
```

---

# 2. System Requirements

## Minimum Requirements

| Component | Requirement             |
| --------- | ----------------------- |
| OS        | Windows / Linux / macOS |
| RAM       | 16 GB recommended       |
| CPU       | 4 cores                 |
| Storage   | 20 GB free              |
| Python    | 3.12+                   |
| Node.js   | 22+                     |
| Docker    | Latest                  |

---

# 3. Required Software

Install:

## Git

Verify:

```bash
git --version
```

---

## Python

Verify:

```bash
python --version
```

Required:

```
Python 3.12+
```

---

## Node.js

Verify:

```bash
node --version
```

Required:

```
Node.js 22+
```

---

## Docker

Verify:

```bash
docker --version
```

---

# 4. Clone Repository

```bash
git clone <repository-url>

cd ai-evaluation-platform
```

---

# 5. Environment Setup

Copy environment file:

Linux/macOS:

```bash
cp .env.example .env
```

Windows:

```powershell
copy .env.example .env
```

Update:

```
DATABASE_URL

REDIS_URL

SECRET_KEY

MODEL_API_KEYS
```

---

# 6. Start Infrastructure

Start database services:

```bash
docker compose up -d postgres redis
```

Verify:

```bash
docker ps
```

Expected:

```
postgres running

redis running
```

---

# 7. Backend Setup

Navigate:

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate:

Windows:

```powershell
.venv\Scripts\activate
```

Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 8. Database Migration

Run:

```bash
alembic upgrade head
```

Verify database:

```bash
psql
```

---

# 9. Start Backend

Run:

```bash
uvicorn app.main:app --reload
```

Backend:

```
http://localhost:8000
```

API Docs:

```
http://localhost:8000/docs
```

---

# 10. Frontend Setup

Navigate:

```bash
cd frontend
```

Install packages:

```bash
npm install
```

Start:

```bash
npm run dev
```

Frontend:

```
http://localhost:5173
```

---

# 11. Start All Services

Using Docker:

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

---

# 12. Development Workflow

Daily workflow:

```
Pull Latest Code

        |

Start Docker Services

        |

Run Backend

        |

Run Frontend

        |

Develop Feature

        |

Run Tests

        |

Commit Changes
```

---

# 13. Running Tests

Backend:

```bash
pytest
```

Frontend:

```bash
npm test
```

---

# 14. Code Quality Checks

Backend:

Run formatter:

```bash
ruff format .
```

Lint:

```bash
ruff check .
```

---

# 15. Debugging

View logs:

```bash
docker compose logs
```

Specific service:

```bash
docker compose logs backend
```

---

# 16. Common Issues

## Port Already Used

Example:

```
Port 5432 already in use
```

Solution:

Stop existing service or change port.

---

## Database Connection Error

Check:

```
DATABASE_URL
```

Verify:

```
PostgreSQL container running
```

---

## Redis Connection Error

Check:

```
REDIS_URL
```

Verify:

```
Redis container running
```

---

# 17. Local AI Model Support

For local inference:

Supported:

- Ollama
- Local LLMs

Example:

```
Model Gateway

        |

Ollama

        |

Local Model
```

---

# 18. Production Difference

Local:

```
Docker Compose

Single Machine
```

Production:

```
Kubernetes

Multiple Nodes

Cloud Services
```

---

# Summary

This guide enables developers to:

- Setup development environment
- Run all services locally
- Debug issues
- Contribute safely

The same workflow scales from local development to production deployment.
