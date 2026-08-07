# AI Evaluation Platform

# Authentication API Design

## 1. Introduction

This document defines the authentication system for the AI Evaluation Platform.

The authentication system provides:

- User registration
- Login
- JWT based authentication
- Token validation
- Role based authorization

Technology:

- FastAPI Security
- JWT
- OAuth2 compatible flow

---

# 2. Authentication Architecture

```
                User

                 |

          React Frontend

                 |

            Backend API

                 |

        Authentication Service

                 |

            PostgreSQL

                 |

              Users
```

---

# 3. Authentication Flow

## User Registration

Flow:

```
User

 |

Register Request

 |

Backend API

 |

Validate Data

 |

Hash Password

 |

Create User

 |

Return User Information
```

---

## Login Flow

```
User

 |

Email + Password

 |

Backend API

 |

Verify Credentials

 |

Generate JWT Token

 |

Return Access Token
```

---

# 4. JWT Token Architecture

Token contains:

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "organization_id": "org_id",
  "role": "developer",
  "exp": "timestamp"
}
```

---

# 5. Token Types

## Access Token

Purpose:

- API authentication

Lifetime:

```
15-60 minutes
```

---

## Refresh Token

Purpose:

- Generate new access tokens

Lifetime:

```
7-30 days
```

---

# 6. API Endpoints

## Register User

Endpoint:

```
POST /api/v1/auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password",
  "first_name": "John",
  "last_name": "Doe"
}
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com"
}
```

---

# Login

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
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer"
}
```

---

# Refresh Token

Endpoint:

```
POST /api/v1/auth/refresh
```

Request:

```json
{
  "refresh_token": "token"
}
```

Response:

```json
{
  "access_token": "new_token"
}
```

---

# Logout

Endpoint:

```
POST /api/v1/auth/logout
```

Actions:

- Invalidate refresh token
- Clear session

---

# 7. Password Security

Passwords are never stored directly.

Process:

```
Password

 |

Hash Function

 |

Password Hash

 |

Database
```

Recommended:

- bcrypt
- Argon2

---

# 8. Authorization Flow

Authentication:

```
Who are you?
```

Authorization:

```
What can you access?
```

Flow:

```
Request

 |

JWT Validation

 |

User Identity

 |

Permission Check

 |

Resource Access
```

---

# 9. Role Based Access Control

Roles:

## Platform Admin

Access:

- All organizations
- Platform settings

---

## Organization Admin

Access:

- Manage members
- Manage projects

---

## Developer

Access:

- Create evaluations
- Manage datasets

---

## Viewer

Access:

- View reports

---

# 10. FastAPI Implementation

Example dependency:

```python
current_user = Depends(get_current_user)
```

Flow:

```
Request

 |

JWT Middleware

 |

Decode Token

 |

Load User

 |

Continue Request
```

---

# 11. Security Rules

## Token Security

- HTTPS only
- Short access token lifetime
- Secure refresh tokens

---

## API Protection

Protected routes:

```
/projects

/evaluations

/datasets

/reports
```

Public routes:

```
/auth/register

/auth/login
```

---

# 12. Future Authentication Support

## OAuth Providers

Planned:

- Google OAuth
- GitHub OAuth
- Microsoft Entra ID

---

## Enterprise SSO

Future:

- SAML
- OIDC
- Active Directory

---

# 13. Audit Events

Authentication events:

```
USER_REGISTERED

USER_LOGIN

USER_LOGOUT

LOGIN_FAILED

PASSWORD_CHANGED
```

Stored in:

```
audit_logs
```

---

# Summary

The authentication architecture provides:

- Secure user identity management
- JWT authentication
- RBAC support
- Enterprise SSO readiness

This design supports both open-source deployment and future SaaS requirements.
