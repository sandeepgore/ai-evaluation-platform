# AI Evaluation Platform

# Authentication Flow

## 1. Introduction

This document defines the authentication architecture of the AI Evaluation Platform.

The authentication system provides:

- Secure user login
- Token-based authentication
- Organization access control
- API security
- Enterprise-ready identity management

---

# 2. Authentication Architecture

High-level flow:

```
                User

                 |

          React Frontend

                 |

          Backend API

                 |

       Authentication Service

                 |

          User Database

```

---

# 3. Authentication Methods

Supported methods:

## Email and Password

```
Email

+

Password

+

Password Hash Verification
```

---

## Enterprise Authentication (Future)

Supported:

- OAuth2
- SAML
- OpenID Connect
- SSO

Providers:

- Google Workspace
- Microsoft Entra ID
- Okta

---

# 4. Login Flow

Sequence:

```
User

 |

Enter Credentials

 |

Frontend

 |

POST /api/v1/auth/login

 |

Backend

 |

Validate User

 |

Generate Tokens

 |

Return Response

 |

Frontend Stores Session

```

---

# 5. Login API

Endpoint:

```
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer"
}
```

---

# 6. JWT Architecture

JWT contains:

```json
{
  "user_id": "123",
  "organization_id": "456",
  "role": "admin",
  "exp": "timestamp"
}
```

Purpose:

- Identify user
- Identify tenant
- Verify permissions

---

# 7. Token Lifecycle

```
Login

 |

Access Token Generated

 |

API Requests

 |

Access Token Expired

 |

Refresh Token Used

 |

New Access Token Generated

```

---

# 8. Access Token

Properties:

```
Short Lifetime

Example:

15 minutes
```

Used for:

- API authentication
- User identity

---

# 9. Refresh Token

Properties:

```
Long Lifetime

Example:

7 days
```

Used for:

- Generate new access tokens
- Maintain sessions

---

# 10. API Request Authentication

Request:

```
GET /api/v1/projects
```

Header:

```
Authorization:

Bearer <access_token>
```

Flow:

```
Request

 |

JWT Middleware

 |

Token Validation

 |

User Context Created

 |

API Execution

```

---

# 11. Authentication Middleware

Location:

```
backend/app/middleware/auth.py
```

Responsibilities:

- Extract JWT
- Validate signature
- Check expiration
- Load user context

---

# 12. Password Security

Passwords are never stored directly.

Storage:

```
Plain Password

        |

Hash Function

        |

Stored Hash
```

Recommended:

```
bcrypt

or

argon2
```

---

# 13. Role Based Access Control

Roles:

```
Owner

Admin

Member

Viewer
```

Example:

| Role   | Permission      |
| ------ | --------------- |
| Owner  | Full access     |
| Admin  | Manage projects |
| Member | Run evaluations |
| Viewer | Read only       |

---

# 14. Authorization Flow

```
User Request

        |

Authentication

        |

Identify User

        |

Check Role

        |

Check Permission

        |

Allow / Reject
```

---

# 15. Organization Context

Every request contains:

```
organization_id
```

Example:

```
User

 |

Organization

 |

Projects

 |

Evaluations
```

This enables multi-tenancy.

---

# 16. Logout Flow

```
User

 |

Logout Request

 |

Invalidate Refresh Token

 |

Clear Session

```

Endpoint:

```
POST /api/v1/auth/logout
```

---

# 17. Security Practices

Implemented:

- HTTPS only
- Secure cookies
- Token expiration
- Password hashing
- Rate limiting
- Audit logging

---

# 18. Future Enterprise Authentication

Planned:

## SSO

```
Enterprise Identity Provider

        |

SAML/OIDC

        |

AI Evaluation Platform
```

---

# 19. Audit Events

Track:

- Login success
- Login failure
- Password change
- Token refresh
- Permission changes

Example:

```
USER_LOGIN_SUCCESS

USER_LOGIN_FAILED

ROLE_UPDATED
```

---

# Summary

Authentication architecture provides:

- Secure API access
- JWT-based authentication
- Multi-tenant identity management
- Enterprise SSO readiness
