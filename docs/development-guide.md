# Development Guide

## Overview

This guide explains how to set up, develop, test, and contribute to the AI Evaluation Platform.

It is intended for:

- Developers
- Contributors
- Maintainers
- AI researchers working with the platform

---

# Development Philosophy

The platform follows these principles:

- Clean architecture
- Modular services
- API-first development
- Test-driven improvements
- Documentation-driven decisions
- Security by default

---

# Repository Structure

```
ai-evaluation-platform/


├── backend/


├── frontend/


├── evaluation-engine/


├── model-gateway/


├── workers/


├── shared/


├── infrastructure/


├── datasets/


├── benchmarks/


├── configs/


├── scripts/


└── docs/

```

---

# Development Environment

## Required Software

Install:

| Tool       | Version |
| ---------- | ------- |
| Python     | 3.12+   |
| Node.js    | 22+     |
| PostgreSQL | 16+     |
| Redis      | 7+      |
| Docker     | Latest  |
| Git        | Latest  |

---

# Initial Setup

## Clone Repository

```bash
git clone <repository-url>

cd ai-evaluation-platform

```

---

# Backend Setup

Navigate:

```bash
cd backend
```

Create environment:

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

Run:

```bash
npm run dev
```

---

# Database Setup

Create PostgreSQL database:

```sql
CREATE DATABASE ai_evaluation;
```

Run migrations:

```bash
alembic upgrade head
```

---

# Redis Setup

Redis is used for:

- Background jobs
- Caching
- Task queues

Start Redis:

```bash
redis-server
```

---

# Docker Development

Start all services:

```bash
docker compose up
```

Stop services:

```bash
docker compose down
```

---

# Development Workflow

Typical workflow:

```
Create Branch


      |


Implement Feature


      |


Write Tests


      |


Run Validation


      |


Create Pull Request


      |


Code Review


      |


Merge

```

---

# Branch Strategy

Branches:

```
main

 |

develop

 |

feature/*

bugfix/*

hotfix/*

```

Example:

```bash
git checkout -b feature/add-rag-evaluation
```

---

# Coding Standards

## Python

Follow:

- PEP8
- Type hints
- Clean functions
- Clear naming

Example:

```python
def calculate_score(
    result: EvaluationResult
) -> float:
    pass

```

---

## TypeScript

Follow:

- Strict typing
- Component reuse
- Functional components
- ESLint rules

---

# Testing Strategy

## Backend Tests

Run:

```bash
pytest
```

Includes:

- Unit tests
- API tests
- Integration tests

---

## Frontend Tests

Run:

```bash
npm run test
```

Includes:

- Component testing
- User interaction testing

---

## Evaluation Tests

Validate:

- Metric calculation
- Dataset processing
- Model responses

---

# API Development

API guidelines:

- Version APIs
- Validate requests
- Return consistent responses
- Document endpoints

Example:

```
/api/v1/evaluations

```

---

# Adding New Feature

Steps:

## 1. Requirement

Update:

```
docs/prd/

```

---

## 2. Architecture

Create ADR if required:

```
docs/adr/

```

---

## 3. Implementation

Update:

```
backend/

frontend/

evaluation-engine/

```

---

## 4. Testing

Add:

- Unit tests
- Integration tests
- Documentation

---

# AI Evaluation Development

When adding evaluation capability:

Follow:

```
Define Metric


      |


Create Evaluator


      |


Add Dataset


      |


Validate Results


      |


Document

```

---

# Debugging

## Backend Logs

Check:

```
application logs

```

## Worker Logs

Check:

```
queue processing logs

```

## Model Logs

Check:

```
provider responses

latency

token usage

```

---

# Environment Variables

Never commit:

```
.env

API keys

Secrets

Credentials

```

Use:

```
.env.example

```

for documentation.

---

# Pull Request Guidelines

Every PR should include:

- Clear description
- Related issue
- Tests
- Documentation updates
- Screenshots for UI changes

---

# Commit Convention

Use:

```
type(scope): message

```

Examples:

```
feat(evaluation): add faithfulness metric

fix(api): handle timeout error

docs(readme): update setup guide

```

---

# Code Review Checklist

Review:

- Code quality
- Security
- Performance
- Tests
- Documentation

---

# Release Process

```
Development


    |


Testing


    |


Staging


    |


Production Release

```

---

# Useful Commands

Backend:

```bash
uvicorn app.main:app --reload
```

Frontend:

```bash
npm run dev
```

Tests:

```bash
pytest

npm run test
```

Docker:

```bash
docker compose up
```

---

# Documentation Updates

Any major change should update:

- Architecture docs
- ADRs
- API docs
- README files

---

# Summary

This guide provides the standard development workflow for building, testing, and maintaining the AI Evaluation Platform.

Following these practices ensures the platform remains scalable, reliable, and easy to contribute to.
