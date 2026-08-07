# Git Branching Strategy

## Overview

This document defines the Git workflow used for the AI Evaluation Platform.

The strategy supports:

- Open-source contribution
- Startup team collaboration
- Continuous development
- Stable releases
- Production deployments

---

# Repository Model

The project follows a trunk-based development approach with feature branches.

```
main

 |

 |

feature branches

 |

 |

Pull Request

 |

 |

main

```

---

# Main Branch

## main

Purpose:

- Production-ready code
- Stable releases
- Deployment source

Rules:

- Direct commits are not allowed
- Requires pull request
- Requires review
- CI checks must pass

---

# Development Branch

## develop (optional)

Purpose:

- Integration testing
- Multiple feature integration

Workflow:

```
feature

   |

develop

   |

main

```

For early startup phase:

```
feature

   |

main

```

is acceptable.

---

# Branch Naming Convention

## Feature Branches

Format:

```
feature/<name>

```

Examples:

```
feature/evaluation-dashboard

feature/model-comparison

feature/rag-metrics

```

---

## Bug Fix Branches

Format:

```
fix/<name>

```

Examples:

```
fix/login-error

fix/metric-calculation

```

---

## Hotfix Branches

Format:

```
hotfix/<name>

```

Examples:

```
hotfix/security-patch

```

---

## Documentation Branches

Format:

```
docs/<name>

```

Examples:

```
docs/api-documentation

docs/architecture-update

```

---

# Commit Message Convention

Use Conventional Commits.

Format:

```
type(scope): description

```

Examples:

```
feat(evaluation): add faithfulness metric


fix(api): handle timeout errors


docs(architecture): update system diagram


test(worker): add queue tests

```

---

# Commit Types

| Type     | Purpose          |
| -------- | ---------------- |
| feat     | New feature      |
| fix      | Bug fix          |
| docs     | Documentation    |
| test     | Testing          |
| refactor | Code improvement |
| perf     | Performance      |
| chore    | Maintenance      |
| security | Security update  |

---

# Pull Request Workflow

```
Developer


   |


Create Branch


   |


Implement Feature


   |


Run Tests


   |


Create PR


   |


CI Pipeline


   |


Code Review


   |


Merge

```

---

# Pull Request Requirements

Every PR must include:

## Description

Explain:

- What changed
- Why it changed
- How it was tested

---

## Checklist

Example:

```
[x] Tests added

[x] Documentation updated

[x] No breaking changes

[x] Security reviewed

```

---

# Code Review Rules

Reviewers should check:

## Code Quality

- Maintainability
- Readability
- Architecture alignment

## Security

- Secrets
- Permissions
- Data handling

## Performance

- Database queries
- API latency
- Resource usage

---

# Release Strategy

Versioning follows Semantic Versioning.

Format:

```
MAJOR.MINOR.PATCH

```

Example:

```
1.4.2

```

Meaning:

```
1 = Breaking changes

4 = New features

2 = Bug fixes

```

---

# Release Flow

```
Feature Complete


        |


Release Branch


        |


Testing


        |


Production Release


        |


Tag Version

```

Example:

```
release/v1.0.0

```

---

# Git Tags

Production versions use tags.

Example:

```
git tag v1.0.0

git push origin v1.0.0

```

---

# Emergency Fix Process

For critical production issues:

```
main


 |

hotfix branch


 |

Fix


 |

Review


 |

Deploy

```

---

# Monorepo Rules

Because this is a monorepo:

Changes should identify affected areas.

Example:

```
feat(evaluation-engine):

Added hallucination evaluator


Affected:

evaluation-engine

docs

```

---

# AI Experiment Branches

AI experiments should use:

```
experiment/<name>

```

Examples:

```
experiment/rag-reranker

experiment/judge-model

experiment/prompt-optimization

```

---

# Summary

This branching strategy provides a simple but scalable workflow suitable for both open-source contributors and future enterprise development teams.
