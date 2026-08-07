# Frontend Dashboard

## Overview

The Frontend Dashboard is the user interface for the AI Evaluation Platform.

It provides an interactive experience for:

- Managing projects
- Configuring evaluations
- Running AI benchmarks
- Viewing evaluation reports
- Monitoring AI quality metrics

The frontend communicates with the Backend API through REST APIs.

---

# Architecture

```
                    User

                     |

                     |

              React Application

                     |

        ----------------------------

        |                          |

    API Services              State Management

        |                          |

        ----------------------------

                     |

              Backend API

```

---

# Technology Stack

| Component         | Technology       |
| ----------------- | ---------------- |
| Framework         | React            |
| Language          | TypeScript       |
| Build Tool        | Vite             |
| Styling           | CSS / UI Library |
| State Management  | Store Layer      |
| Testing           | Vitest           |
| API Communication | REST             |

---

# Directory Structure

```
frontend/


├── src/


│


├── app/

│   Application initialization


│


├── components/

│   Reusable UI components


│


├── features/

│   Feature-based modules


│


├── hooks/

│   Custom React hooks


│


├── services/

│   API communication layer


│


├── store/

│   Application state


│


└── utils/

    Shared utilities


```

---

# Application Modules

## Dashboard

Provides:

- Evaluation overview
- Model comparison
- Quality scores
- Recent activity

---

## Projects

Features:

- Create projects
- Manage datasets
- Configure evaluation pipelines

---

## Evaluation Reports

Displays:

- Overall score
- Individual metrics
- Model comparison
- Recommendations

---

## Model Management

Supports:

- AI provider configuration
- Model selection
- Model performance tracking

---

# Setup

## Requirements

Install:

```
Node.js >= 22

npm >= 10

```

---

# Installation

Navigate:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

---

# Environment Variables

Create:

```
.env

```

Example:

```env
VITE_API_URL=http://localhost:8000
```

---

# Development

Start development server:

```bash
npm run dev
```

Application:

```
http://localhost:5173

```

---

# Production Build

Create production build:

```bash
npm run build
```

Preview build:

```bash
npm run preview
```

---

# API Integration

API calls are separated into service modules.

Example:

```
services/


    auth.service.ts


    evaluation.service.ts


    project.service.ts

```

Benefits:

- Clean separation
- Easy testing
- Provider replacement

---

# State Management

Application state is organized by domain.

Example:

```
store/


├── auth

├── projects

├── evaluations

└── models

```

---

# Component Guidelines

Components should be:

- Reusable
- Small
- Type-safe
- Independent

Example:

```
EvaluationCard

MetricChart

ScoreBadge

ReportTable

```

---

# Testing

Run tests:

```bash
npm run test
```

Component testing:

- Rendering
- User interactions
- State changes
- API behavior

---

# Code Quality

Lint:

```bash
npm run lint
```

Formatting:

```bash
npm run format
```

---

# Deployment

Production deployment options:

- Docker
- Kubernetes
- Static hosting

Docker build:

```bash
docker build -t ai-evaluation-frontend .
```

---

# Security

Frontend follows:

- Secure API communication
- No secret keys in frontend
- Input validation
- Protected routes

---

# Future Improvements

Planned:

- Advanced analytics dashboard
- Real-time evaluation streaming
- Interactive charts
- AI quality recommendations
- Custom dashboards

---

# Summary

The frontend provides a modern, scalable interface for managing AI evaluations and monitoring AI system quality.
