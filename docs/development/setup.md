# Development Setup Guide

## Overview

This document explains how to set up the AI Evaluation Platform development environment.

The platform is designed as a monorepo containing:

- Backend API
- Frontend Dashboard
- Evaluation Engine
- Model Gateway
- Worker Services
- Infrastructure Components

---

# Prerequisites

## Required Software

Install the following:

### Git

Version:

```
>= 2.40
```

### Python

Version:

```
Python 3.12+
```

### Node.js

Version:

```
Node.js 22+
```

### Docker

Version:

```
Docker 24+
```

### Docker Compose

Version:

```
Docker Compose v2+
```

---

# Clone Repository

```bash
git clone https://github.com/<organization>/ai-evaluation-platform.git

cd ai-evaluation-platform
```

---

# Environment Configuration

Copy environment file:

```bash
cp .env.example .env
```

Configure:

```
DATABASE_URL=

REDIS_URL=

OPENAI_API_KEY=

GEMINI_API_KEY=

ANTHROPIC_API_KEY=

SECRET_KEY=

```

---

# Local Development Architecture

```
Developer Machine


        |

        |

Docker Compose


--------------------------------


PostgreSQL


Redis


Backend API


Workers


Frontend


```

---

# Backend Setup

Navigate:

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv venv
```

Activate:

Windows:

```powershell
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```
http://localhost:8000
```

API Documentation:

```
http://localhost:8000/docs
```

---

# Frontend Setup

Navigate:

```bash
cd frontend
```

Install packages:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

Frontend URL:

```
http://localhost:5173
```

---

# Evaluation Engine Setup

Navigate:

```bash
cd evaluation-engine
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

---

# Worker Setup

Navigate:

```bash
cd workers
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start worker:

```bash
python worker.py
```

---

# Docker Development

Start all services:

```bash
docker compose up
```

Run in background:

```bash
docker compose up -d
```

Stop:

```bash
docker compose down
```

---

# Database Setup

Run migrations:

```bash
make migrate
```

Create seed data:

```bash
python scripts/seed.py
```

---

# Code Quality Tools

## Python

Formatting:

```bash
ruff format .
```

Linting:

```bash
ruff check .
```

Testing:

```bash
pytest
```

---

## Frontend

Lint:

```bash
npm run lint
```

Build:

```bash
npm run build
```

---

# Development Workflow

```
Create Branch

      |

Implement Feature

      |

Run Tests

      |

Create Pull Request

      |

Code Review

      |

Merge

```

---

# Common Issues

## Docker Port Conflict

Check running containers:

```bash
docker ps
```

Stop conflicting service:

```bash
docker stop <container>
```

---

## Database Connection Error

Verify:

```
PostgreSQL running

Environment variables configured

Migration completed

```

---

# Recommended IDE

Recommended:

- VS Code
- PyCharm

Extensions:

- Python
- ESLint
- Prettier
- Docker
- GitLens

---

# Summary

Following this setup guide provides a complete local development environment for contributing to the AI Evaluation Platform.
