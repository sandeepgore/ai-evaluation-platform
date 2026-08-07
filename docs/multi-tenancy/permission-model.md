# AI Evaluation Platform

# Permission Model

## 1. Introduction

This document defines the authorization and permission model used in the AI Evaluation Platform.

The permission system provides:

- Secure resource access
- Role-based authorization
- Tenant-level isolation
- Enterprise governance

The model follows:

```
User

 |

Role

 |

Permission

 |

Resource

```

---

# 2. Authorization Architecture

Request flow:

```
User Request

      |

Authentication

      |

Identify User

      |

Load Organization Context

      |

Check Role

      |

Check Permission

      |

Access Resource

```

---

# 3. Access Control Model

The platform uses:

```
RBAC

+

Resource Level Permissions

+

Tenant Isolation
```

---

# 4. Roles

Default roles:

## Owner

Full organization access.

Permissions:

```
*

```

Can:

- Manage organization
- Manage billing
- Manage users
- Delete workspace

---

## Admin

Organization administrator.

Permissions:

```
users.manage

projects.manage

settings.manage

```

---

## Member

Standard user.

Permissions:

```
projects.create

projects.update

evaluations.run

datasets.upload

```

---

## Viewer

Read-only user.

Permissions:

```
projects.read

evaluations.read

reports.read

```

---

# 5. Permission Structure

Format:

```
resource.action
```

Examples:

```
project.create

project.read

project.update

project.delete
```

---

# 6. Permission Categories

## Organization Permissions

Examples:

```
organization.read

organization.update

organization.delete
```

---

## User Permissions

Examples:

```
user.invite

user.remove

user.update_role
```

---

## Project Permissions

Examples:

```
project.create

project.read

project.update

project.delete
```

---

## Evaluation Permissions

Examples:

```
evaluation.create

evaluation.run

evaluation.cancel

evaluation.read
```

---

## Dataset Permissions

Examples:

```
dataset.upload

dataset.read

dataset.delete
```

---

## Model Permissions

Examples:

```
model.configure

model.use

model.manage
```

---

# 7. Permission Matrix

| Permission          | Owner | Admin | Member | Viewer |
| ------------------- | ----- | ----- | ------ | ------ |
| Manage Organization | ✅    | ❌    | ❌     | ❌     |
| Invite Users        | ✅    | ✅    | ❌     | ❌     |
| Create Projects     | ✅    | ✅    | ✅     | ❌     |
| Run Evaluations     | ✅    | ✅    | ✅     | ❌     |
| View Reports        | ✅    | ✅    | ✅     | ✅     |
| Delete Projects     | ✅    | ✅    | ❌     | ❌     |

---

# 8. Resource Level Authorization

Example:

Project:

```
Project A

Organization X

Owner: User 1

```

User request:

```
GET /projects/A
```

Validation:

```
User belongs to Organization X

        +

User has project.read permission

        |

Allow Access
```

---

# 9. Database Permission Model

Tables:

## Roles

```
roles

----------------

id

name

organization_id

```

---

## Permissions

```
permissions

----------------

id

name

resource

action

```

---

## Role Permissions

```
role_permissions


role_id

permission_id

```

---

## User Roles

```
user_roles


user_id

role_id

```

---

# 10. Custom Roles

Enterprise customers may create custom roles.

Example:

```
AI Researcher

Permissions:

dataset.upload

evaluation.run

model.use
```

---

# 11. API Authorization Example

Request:

```
POST /api/v1/evaluations
```

Flow:

```
Authenticate User

        |

Get Organization

        |

Check:

evaluation.create

        |

Execute Request

```

---

# 12. Permission Middleware

Location:

```
backend/app/middleware/auth.py
```

Responsibilities:

- Validate identity
- Load permissions
- Enforce access rules

---

# 13. Background Job Permissions

Workers must validate:

```
Tenant ID

+

User Permission

+

Resource Access
```

Example:

```
Evaluation Job


{
organization_id:"123",
project_id:"456"
}

```

---

# 14. Audit Logging

Permission changes are tracked.

Events:

```
ROLE_CREATED

ROLE_UPDATED

USER_PERMISSION_CHANGED

ACCESS_DENIED
```

---

# 15. Security Rules

Rules:

- Default deny access
- Verify tenant ownership
- Avoid privilege escalation
- Audit sensitive actions
- Apply least privilege

---

# 16. Enterprise Features

Future support:

- Attribute Based Access Control (ABAC)
- Policy engine
- Approval workflows
- Fine-grained permissions

---

# Summary

The permission model enables:

- Secure SaaS authorization
- Enterprise RBAC
- Custom roles
- Resource-level security

Principle:

```
Every request must prove:

Who are you?

Which organization?

What can you access?
```
