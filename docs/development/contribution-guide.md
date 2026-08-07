# Contribution Guide

## Overview

Thank you for contributing to the AI Evaluation Platform.

This guide explains how developers, researchers, and community members can contribute code, documentation, evaluations, and ideas.

The project welcomes contributions in:

- Backend development
- Frontend development
- AI evaluation metrics
- Model integrations
- Documentation
- Testing
- Infrastructure improvements

---

# Code of Conduct

All contributors are expected to:

- Communicate respectfully
- Provide constructive feedback
- Follow engineering standards
- Respect intellectual property
- Avoid sharing confidential information

---

# Getting Started

## 1. Fork Repository

Create your own fork:

```
GitHub Repository

        |

Your Fork

```

---

## 2. Clone Repository

```bash
git clone <repository-url>

cd ai-evaluation-platform

```

---

## 3. Setup Development Environment

Follow:

```
docs/development/setup.md

```

---

# Contribution Workflow

```
Find Issue


    |


Create Branch


    |


Implement Change


    |


Add Tests


    |


Create Pull Request


    |


Code Review


    |


Merge

```

---

# Creating Issues

Before implementing large changes, create an issue.

Issue should contain:

## Feature Request

Include:

- Problem statement
- Proposed solution
- Expected impact

Example:

```
Problem:

Users cannot compare evaluation runs.


Solution:

Add model comparison dashboard.


```

---

## Bug Report

Include:

- Description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs/screenshots

Example:

```
Bug:

Evaluation report generation fails.


Steps:

1. Upload dataset

2. Start evaluation


Expected:

Report generated


Actual:

Worker timeout

```

---

# Branch Creation

Follow:

```
feature/<name>

fix/<name>

docs/<name>

experiment/<name>

```

Example:

```bash
git checkout -b feature/custom-evaluator
```

---

# Development Rules

Before submitting:

## Code Quality

Ensure:

- Clean implementation
- Proper naming
- Type safety
- No unnecessary dependencies

---

## Tests

Add tests for:

- New features
- Bug fixes
- Evaluation metrics
- API changes

---

## Documentation

Update documentation when changing:

- APIs
- Architecture
- Configuration
- User workflows

---

# Pull Request Guidelines

A good PR should include:

## Title

Use:

```
feat(scope): description

```

Example:

```
feat(metrics): add hallucination evaluator

```

---

## Description Template

```
## What changed?


## Why?


## Testing Done?


## Screenshots (if UI change)


## Documentation Updated?

```

---

# Review Process

Pull requests are reviewed for:

## Correctness

Does it solve the problem?

## Architecture

Does it follow platform design?

## Security

Does it introduce risks?

## Performance

Does it affect scalability?

---

# AI Evaluation Contributions

Contributors can add:

## New Evaluators

Examples:

- Bias evaluator
- Toxicity evaluator
- Custom domain evaluator

Requirements:

- Clear metric definition
- Test dataset
- Expected output
- Documentation

---

## New Model Providers

Provider additions require:

- Provider interface implementation
- Authentication handling
- Error handling
- Cost calculation support

---

# Documentation Contributions

Documentation improvements are welcome:

Examples:

- Architecture diagrams
- Tutorials
- Examples
- API documentation

---

# Commit Guidelines

Use:

```
type(scope): message

```

Examples:

```
feat(engine): add RAG evaluator


fix(worker): handle retry failure


docs(api): update authentication guide

```

---

# Security Reporting

Do not create public issues for security vulnerabilities.

Report privately with:

- Vulnerability description
- Impact
- Reproduction steps

---

# Community Contributions

Future community areas:

- Evaluation datasets
- Benchmark tasks
- Custom plugins
- Model adapters
- Research improvements

---

# Maintainer Responsibilities

Maintainers should:

- Review contributions
- Maintain roadmap
- Ensure quality standards
- Support contributors

---

# Summary

This contribution guide provides a structured workflow for developers and researchers to collaborate on building an open and enterprise-ready AI Evaluation Platform.
