# AI Evaluation Platform

# Organization Model

## 1. Introduction

This document defines the organization model used in the AI Evaluation Platform.

An organization represents a customer workspace that manages:

- Users
- Teams
- Projects
- Models
- Datasets
- Evaluations
- Billing

The organization is the primary tenant boundary.

---

# 2. Organization Architecture

```
Platform


    |

Organization


    |

--------------------------------


Users

Teams

Projects

Datasets

Models

Evaluations

Reports


--------------------------------

```

---

# 3. Organization Entity

Database model:

```
organizations

----------------------------

id

name

slug

plan

status

created_at

updated_at

```

---

# 4. Organization Lifecycle

Organization states:

```
Created

   |

Active

   |

Suspended

   |

Deleted
```

---

# 5. Organization Creation Flow

```
User Signup

      |

Create Account

      |

Create Organization

      |

Assign Owner Role

      |

Create Workspace

      |

Start Using Platform
```

---

# 6. Organization Roles

Default roles:

| Role   | Responsibility                |
| ------ | ----------------------------- |
| Owner  | Full organization control     |
| Admin  | Manage users and resources    |
| Member | Create and manage evaluations |
| Viewer | Read-only access              |

---

# 7. Organization Owner

The owner can:

- Manage subscription
- Invite users
- Delete organization
- Manage permissions
- Access billing

Example:

```
Organization

      |

Owner

      |

Administrators
```

---

# 8. User Membership

Users belong to organizations through membership.

Model:

```
organization_members


id

organization_id

user_id

role

status

created_at

```

---

# 9. Multiple Organization Support

A user can belong to multiple organizations.

Example:

```
User A


 |

------------------

|                |

Company X     Company Y


Admin          Viewer

```

---

# 10. Teams

Organizations can create teams.

Example:

```
Organization


      |

Teams


      |

Members

```

Database:

```
teams


id

organization_id

name

```

---

# 11. Project Ownership

Projects belong to organizations.

Example:

```
Organization

       |

Project


       |

Evaluation Runs

```

Database:

```
projects


id

organization_id

team_id

name

```

---

# 12. Organization Settings

Settings include:

```
organization_settings


------------------------

organization_id

timezone

security_settings

notification_settings

```

---

# 13. Subscription Plans

Organization plan:

```
Free

 |

Professional

 |

Enterprise
```

Plan controls:

- User limits
- Evaluation limits
- Storage
- API access

---

# 14. Feature Management

Feature access:

```
Organization Plan

        |

Feature Flags

        |

Enabled Features
```

Example:

Enterprise:

```
Advanced Analytics

SSO

Dedicated Models
```

---

# 15. Organization Suspension

Reasons:

- Payment failure
- Security violation
- Admin action

Flow:

```
Active

 |

Suspended

 |

Recovery

 |

Active
```

---

# 16. Organization Deletion

Deletion process:

```
Delete Request

       |

Confirmation

       |

Data Export

       |

Soft Delete

       |

Permanent Removal
```

---

# 17. Audit Tracking

Track organization events:

Examples:

```
ORGANIZATION_CREATED

USER_INVITED

ROLE_CHANGED

PLAN_UPDATED

ORGANIZATION_DELETED
```

---

# 18. Enterprise Organization Model

Enterprise customers may require:

```
Organization

      |

Departments

      |

Teams

      |

Projects
```

Example:

```
Healthcare Company


 |

AI Research Team


 |

Evaluation Projects
```

---

# 19. Future Enhancements

Planned:

- Organization hierarchy
- Multiple workspaces
- Custom roles
- Advanced policies
- Enterprise governance

---

# Summary

The organization model provides:

- SaaS workspace management
- Enterprise scalability
- Secure ownership boundaries
- Flexible team collaboration

Core principle:

```
Organization = Customer Boundary
```
