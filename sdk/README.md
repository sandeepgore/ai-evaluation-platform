# SDK

## Overview

The SDK provides developer-friendly interfaces for integrating external applications with the AI Evaluation Platform.

It allows developers to:

- Submit evaluation jobs
- Manage projects
- Upload datasets
- Retrieve evaluation results
- Automate AI quality workflows

---

# Purpose

The SDK simplifies platform integration by providing:

- API client abstraction
- Authentication handling
- Request validation
- Response parsing
- Error handling

---

# Architecture

```
External Application


        |


        |


      SDK


        |


        |


 Backend API


        |


 Evaluation Platform

```

---

# Supported Languages

Initial:

```
Python SDK

```

Future:

```
JavaScript SDK

TypeScript SDK

Java SDK

```

---

# Directory Structure

```
sdk/


├── python/


│
├── client/


├── models/


├── exceptions/


└── README.md

```

---

# Installation

Python:

```bash
pip install ai-evaluation-sdk
```

---

# Authentication

The SDK uses API keys.

Example:

```python
from ai_evaluation import Client


client = Client(
    api_key="your_api_key"
)

```

---

# Usage Examples

## Create Project

```python
project = client.projects.create(
    name="Customer Support AI"
)

```

---

## Run Evaluation

```python
evaluation = client.evaluations.run(
    project_id="123",
    dataset_id="456",
    model="gpt-model"
)

```

---

## Get Results

```python
result = client.evaluations.get(
    evaluation_id="789"
)

```

---

# Core Modules

## Projects Client

Handles:

- Create projects
- Update projects
- Manage configurations

---

## Evaluation Client

Handles:

- Start evaluations
- Track progress
- Fetch reports

---

## Dataset Client

Handles:

- Upload datasets
- Validate files
- Manage versions

---

## Model Client

Handles:

- Register models
- Configure providers
- Retrieve model information

---

# Error Handling

SDK provides standardized exceptions.

Example:

```python
try:

    client.evaluations.run()

except EvaluationError:

    print("Evaluation failed")

```

---

# Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt

```

Run tests:

```bash
pytest

```

---

# Versioning

SDK follows semantic versioning.

Example:

```
1.0.0

```

Changes:

```
Major

Breaking API changes


Minor

New features


Patch

Bug fixes

```

---

# Future Improvements

Planned:

- JavaScript SDK
- Streaming responses
- Async client
- CLI tool
- Notebook integration

---

# Summary

The SDK enables developers to integrate AI evaluation capabilities into their own applications with minimal effort.
