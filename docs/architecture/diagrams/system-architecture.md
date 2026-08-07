# AI Evaluation Platform

# System Architecture Diagrams

## 1. High Level System Architecture

```mermaid
flowchart TB

    U[Users]

    F[React Frontend]

    API[Backend API<br/>FastAPI]

    EE[Evaluation Engine]

    MG[Model Gateway]

    W[Worker System]

    DB[(PostgreSQL)]

    R[(Redis)]

    OS[(Object Storage)]

    Providers[AI Providers<br/>OpenAI<br/>Gemini<br/>Anthropic<br/>Ollama]


    U --> F

    F --> API

    API --> EE

    API --> MG

    API --> W

    EE --> DB

    EE --> R

    W --> R

    W --> EE

    MG --> Providers

    API --> DB

    API --> R

    EE --> OS

    W --> OS
```

---

# 2. Evaluation Processing Flow

```mermaid
sequenceDiagram

    participant User
    participant Frontend
    participant API
    participant Queue
    participant Worker
    participant ModelGateway
    participant EvaluationEngine
    participant Database


    User->>Frontend: Start Evaluation

    Frontend->>API: Create Evaluation Request

    API->>Database: Create Evaluation Record

    API->>Queue: Add Evaluation Job

    API-->>Frontend: Return Job ID


    Worker->>Queue: Fetch Job

    Worker->>ModelGateway: Request Model Response

    ModelGateway->>ModelGateway: Select Provider

    ModelGateway-->>Worker: Model Response


    Worker->>EvaluationEngine: Evaluate Response

    EvaluationEngine->>Database: Store Metrics

    Database-->>Frontend: Evaluation Result
```

---

# 3. Backend Internal Architecture

```mermaid
flowchart LR


API[API Layer]

SERVICE[Service Layer]

REPO[Repository Layer]

DB[(Database)]


API --> SERVICE

SERVICE --> REPO

REPO --> DB
```

---

# 4. Evaluation Engine Architecture

```mermaid
flowchart TB


Input[Evaluation Request]


Pipeline[Evaluation Pipeline]


Registry[Evaluator Registry]


Accuracy[Accuracy Evaluator]

Faithfulness[Faithfulness Evaluator]

Relevance[Relevance Evaluator]

Safety[Safety Evaluator]


Aggregator[Score Aggregator]


Report[Report Generator]


Input --> Pipeline

Pipeline --> Registry


Registry --> Accuracy

Registry --> Faithfulness

Registry --> Relevance

Registry --> Safety


Accuracy --> Aggregator

Faithfulness --> Aggregator

Relevance --> Aggregator

Safety --> Aggregator


Aggregator --> Report
```

---

# 5. Model Gateway Architecture

```mermaid
flowchart TB


Application[Application]


Gateway[Model Gateway]


Registry[Provider Registry]


OpenAI[OpenAI Provider]

Gemini[Gemini Provider]

Claude[Anthropic Provider]

Ollama[Ollama Provider]


Application --> Gateway

Gateway --> Registry


Registry --> OpenAI

Registry --> Gemini

Registry --> Claude

Registry --> Ollama
```

---

# 6. Deployment Architecture

```mermaid
flowchart TB


Internet[Internet]


LB[Load Balancer]


Frontend[Frontend Containers]


Backend[Backend Containers]


Workers[Worker Containers]


Evaluation[Evaluation Containers]


Postgres[(PostgreSQL Cluster)]


Redis[(Redis Cluster)]


Storage[(Object Storage)]


Internet --> LB


LB --> Frontend

LB --> Backend


Backend --> Workers

Backend --> Evaluation


Backend --> Postgres

Backend --> Redis


Workers --> Redis

Workers --> Storage

Evaluation --> Postgres

Evaluation --> Storage
```

---

# 7. Future Kubernetes Architecture

```mermaid
flowchart TB


K8S[Kubernetes Cluster]


FrontendPods[Frontend Pods]

BackendPods[Backend Pods]

WorkerPods[Worker Pods]

EvaluationPods[Evaluation Pods]


Services[Internal Services]


Database[(Managed PostgreSQL)]

Cache[(Redis Cluster)]


K8S --> FrontendPods

K8S --> BackendPods

K8S --> WorkerPods

K8S --> EvaluationPods


BackendPods --> Services

Services --> Database

Services --> Cache
```

---

# Diagram Guidelines

All architecture diagrams should:

- Use Mermaid format
- Be version controlled
- Represent actual implementation
- Be updated with major architecture changes

---

# Future Diagrams

Planned additions:

- Database ER diagram
- Authentication flow
- Multi-tenancy architecture
- Evaluation lifecycle
- CI/CD pipeline
- Observability architecture
