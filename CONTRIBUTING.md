# Contribution Guide

## Overview

Thank you for your interest in contributing to the AI Evaluation Platform.

This guide explains how to contribute code, documentation, bug fixes, new evaluation metrics, and feature improvements while maintaining a high-quality codebase.

---

# Our Goals

We aim to build an enterprise-grade open-source AI Evaluation Platform that is:

- Scalable
- Reliable
- Well documented
- Easy to extend
- Community driven

Every contribution, regardless of size, is appreciated.

---

# Ways to Contribute

You can contribute by:

- Fixing bugs
- Developing new features
- Improving documentation
- Writing tests
- Optimizing performance
- Adding evaluation metrics
- Supporting additional AI providers
- Improving the UI
- Reporting issues
- Reviewing pull requests

---

# Before You Start

Before contributing, please:

- Read the project documentation
- Review existing issues
- Search for existing pull requests
- Discuss large changes before implementation

Useful documentation:

```
docs/architecture/
docs/api/
docs/development/
docs/ai-evaluation/
```

---

# Development Setup

Clone the repository:

```bash
git clone https://github.com/your-org/ai-evaluation-platform.git

cd ai-evaluation-platform
```

Follow the setup guide:

```
docs/development/setup.md
```

---

# Branching Strategy

Never commit directly to the `main` branch.

Create a feature branch:

```bash
git checkout -b feature/add-rag-metric
```

Examples:

```
feature/add-openai-provider

feature/add-dashboard

feature/add-faithfulness-score

bugfix/fix-auth-token

docs/update-readme
```

---

# Development Workflow

```
Fork Repository

       │

Clone Repository

       │

Create Feature Branch

       │

Develop Feature

       │

Write Tests

       │

Run Validation

       │

Commit Changes

       │

Push Branch

       │

Open Pull Request

       │

Code Review

       │

Merge
```

---

# Coding Standards

## Python

Follow:

- PEP 8
- Type hints
- Small functions
- Clear variable names
- Docstrings for public methods

Example:

```python
def calculate_accuracy(
    expected: str,
    actual: str
) -> float:
    """Calculate answer accuracy."""
```

---

## TypeScript

Follow:

- Strict typing
- Functional components
- Reusable hooks
- ESLint rules
- Prettier formatting

---

# Commit Message Convention

Use Conventional Commits.

Format:

```
type(scope): description
```

Examples:

```
feat(api): add evaluation endpoint

feat(metrics): add faithfulness evaluator

fix(auth): refresh expired tokens

docs(readme): update installation guide

refactor(workers): simplify queue processing

test(api): add authentication tests

chore(deps): update dependencies
```

---

# Pull Request Guidelines

Each Pull Request should:

- Solve one logical problem
- Include tests (when applicable)
- Update documentation
- Pass CI checks
- Follow coding standards

Provide:

- Summary
- Motivation
- Screenshots (for UI changes)
- Testing performed
- Related issue (if any)

---

# Testing

Run backend tests:

```bash
pytest
```

Run frontend tests:

```bash
npm run test
```

Ensure:

- Existing tests pass
- New functionality is covered
- No regression is introduced

---

# Documentation

Documentation is part of every feature.

When adding functionality, update the relevant files:

- README
- API documentation
- Architecture documentation
- PRD (if applicable)
- ADR (if architectural decisions change)

---

# Reporting Issues

When creating an issue, include:

- Clear title
- Description
- Expected behavior
- Actual behavior
- Steps to reproduce
- Logs or screenshots
- Environment information

---

# Feature Requests

Feature requests should explain:

- Problem being solved
- Proposed solution
- Alternatives considered
- Expected impact

---

# Code Review

Reviewers typically evaluate:

- Correctness
- Readability
- Performance
- Security
- Maintainability
- Test coverage
- Documentation

Feedback is intended to improve the project and should be addressed constructively.

---

# Security

Do not commit:

- API keys
- Passwords
- Secrets
- Tokens
- `.env` files

If you discover a security vulnerability, please report it privately before opening a public issue.

---

# AI Evaluation Contributions

New evaluation metrics should include:

- Metric definition
- Evaluation logic
- Unit tests
- Sample datasets
- Documentation
- Performance considerations

Examples:

- Faithfulness
- Context Precision
- Context Recall
- Hallucination Detection
- Toxicity
- Bias Detection

---

# Model Provider Contributions

When adding a new provider:

- Implement the provider interface
- Add configuration
- Handle authentication
- Normalize responses
- Add retry logic
- Include tests
- Update documentation

---

# Quality Checklist

Before submitting a Pull Request, verify:

- Code builds successfully
- Tests pass
- Documentation is updated
- No secrets are committed
- Linting passes
- Formatting is correct

---

# Recognition

All contributors are appreciated.

Contributions of any size—code, documentation, bug reports, testing, or ideas—help improve the platform for everyone.

---

# License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.

---

# Thank You

Thank you for helping build the AI Evaluation Platform.

Together, we can create a robust open-source platform for evaluating, benchmarking, and improving AI systems.
