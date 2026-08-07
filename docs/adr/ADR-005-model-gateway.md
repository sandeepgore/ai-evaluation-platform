# ADR-005: Model Gateway Architecture

## Status

Accepted

## Date

2026-08-07

## Context

The AI Evaluation Platform needs to support multiple Large Language Model providers.

Supported providers:

- OpenAI
- Google Gemini
- Anthropic Claude
- Ollama Local Models
- Future custom providers

Each provider has different:

- APIs
- Authentication methods
- Request formats
- Response formats
- Pricing models
- Rate limits

Direct integration from every service would create tight coupling.

Example problem:

```
Evaluation Engine

      |

OpenAI API


Evaluation Engine

      |

Gemini API


Evaluation Engine

      |

Anthropic API
```

This creates:

- Duplicate code
- Difficult maintenance
- Provider lock-in

---

# Decision

We will implement a dedicated **Model Gateway Service**.

The Model Gateway acts as an abstraction layer between the platform and AI providers.

Architecture:

```
                 Application Services


                         |


                  Model Gateway


                         |


        ---------------------------------


        |              |                |


     OpenAI         Gemini          Ollama


        |              |                |


     GPT Models    Gemini Models   Local Models


```

---

# Responsibilities

The Model Gateway manages:

## Provider Management

- Provider registration
- Authentication
- API communication

---

## Request Normalization

Convert internal requests:

```
Platform Request

        |

Model Gateway

        |

Provider Specific Format

```

---

## Response Standardization

Different provider responses become:

```json
{
  "content": "response",
  "tokens": 1200,
  "latency": 800,
  "cost": 0.02
}
```

---

## Cost Tracking

Track:

- Input tokens
- Output tokens
- API cost
- Usage per organization

Example:

```
Organization A

    |

GPT Usage

    |

$25.40

```

---

## Rate Limiting

Control:

- Requests per minute
- Token limits
- Provider quotas

---

# Internal Architecture

```
model-gateway/


├── interfaces/

│       base_provider.py


├── providers/

│

├── openai/

├── gemini/

├── anthropic/

└── ollama/


├── routing/


├── cost_tracking/


└── rate_limiting/

```

---

# Provider Interface

All providers follow a common contract.

Example:

```python
class ModelProvider:

    def generate(
        self,
        prompt,
        parameters
    ):
        pass
```

---

# Model Routing

The gateway decides:

```
Request

   |

Routing Rules

   |

Select Provider

   |

Execute Request

```

Routing factors:

- Cost
- Latency
- Quality
- Availability

---

# Example Routing

Low cost requirement:

```
Request

 |

Ollama

 |

Local Model

```

High accuracy requirement:

```
Request

 |

GPT / Claude

 |

Premium Model

```

---

# Observability

Track:

- Request count
- Latency
- Errors
- Token usage
- Cost

Example:

```
Model:

GPT-5


Requests:

10000


Average Latency:

1.2s


Cost:

$150

```

---

# Security

API keys are managed centrally.

Never expose provider credentials to users.

Flow:

```
User

 |

Platform

 |

Model Gateway

 |

Provider

```

---

# Alternatives Considered

## Direct Provider Integration

Rejected.

Reasons:

- Duplicate implementation
- Hard provider switching
- Poor maintainability

---

## LangChain Only

Rejected as the core abstraction.

Reasons:

- Additional dependency
- Less control
- Business logic mixed with framework

LangChain may be used inside evaluation workflows.

---

## Single Provider Architecture

Rejected.

Reasons:

- Vendor lock-in
- No cost optimization
- Reduced flexibility

---

# Consequences

## Benefits

✅ Provider independence  
✅ Easy model switching  
✅ Central cost tracking  
✅ Unified API  
✅ Better observability

---

## Trade-offs

❌ Additional service complexity  
❌ Requires gateway maintenance  
❌ Extra network hop

---

# Future Considerations

Planned improvements:

- Automatic model selection
- AI routing algorithms
- Model quality scoring
- Provider fallback
- Enterprise private models

---

# Summary

The Model Gateway provides a unified interface for interacting with multiple AI providers while enabling cost optimization, observability, and future model flexibility.
