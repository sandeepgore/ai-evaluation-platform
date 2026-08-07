# Model Gateway

## Overview

The Model Gateway is the unified AI provider abstraction layer of the AI Evaluation Platform.

It provides a single interface to interact with multiple Large Language Model providers.

Supported providers:

- OpenAI
- Gemini
- Anthropic
- Ollama
- Local Models

The gateway hides provider-specific implementations and provides consistent model access across the platform.

---

# Architecture

```
                    Applications


                         |


                         |


                  Model Gateway


                         |


        ------------------------------------


        |              |          |          |


     OpenAI        Gemini    Anthropic   Ollama


                         |


                    AI Models

```

---

# Responsibilities

The Model Gateway handles:

- Provider abstraction
- Model routing
- API authentication
- Rate limiting
- Cost tracking
- Retry management
- Response normalization

---

# Technology Stack

| Component     | Technology         |
| ------------- | ------------------ |
| Language      | Python             |
| Architecture  | Provider Pattern   |
| Async Support | AsyncIO            |
| Logging       | Structured Logging |
| Testing       | Pytest             |

---

# Directory Structure

```
model-gateway/


├── interfaces/


│   └── base_provider.py


├── providers/


│
├── openai/


├── gemini/


├── anthropic/


└── ollama/


├── registry/


│   └── provider_registry.py


├── routing/


├── rate_limiting/


└── cost_tracking/

```

---

# Provider Interface

All providers implement a common interface.

Example:

```python
class BaseProvider:

    async def generate(
        self,
        prompt: str
    ):
        pass

```

---

# Supported Providers

## OpenAI

Supports:

- GPT models
- Chat completion
- Embeddings

---

## Gemini

Supports:

- Gemini models
- Google AI integration

---

## Anthropic

Supports:

- Claude models
- Enterprise AI workflows

---

## Ollama

Supports:

- Local LLMs
- Offline development
- Private deployments

---

# Model Routing

The gateway can select models based on:

- Cost
- Latency
- Quality
- Availability

Example:

```
High quality request

        |

        |

GPT-5


```

```
Low cost request

        |

        |

Local Model

```

---

# Cost Tracking

Tracks:

- Token usage
- Request cost
- Provider cost
- Project usage

Example:

```json
{
  "model": "gpt-model",

  "input_tokens": 1200,

  "output_tokens": 500,

  "cost": 0.04
}
```

---

# Rate Limiting

Protects providers from excessive usage.

Supports:

- Request limits
- Token limits
- Organization quotas

---

# Error Handling

Normalized errors:

Example:

```json
{
  "error_code": "MODEL_TIMEOUT",

  "provider": "openai",

  "retryable": true
}
```

---

# Local Development

Install:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

---

# Adding New Provider

Steps:

1. Create provider folder

```
providers/new_provider/

```

2. Implement interface

```
BaseProvider

```

3. Register provider

```
provider_registry.py

```

4. Add tests

5. Update documentation

---

# Security

The gateway manages:

- API key protection
- Secret management
- Request validation
- Usage monitoring

Never expose provider keys to frontend applications.

---

# Future Improvements

Planned:

- Automatic model selection
- Model performance scoring
- A/B testing
- Provider fallback
- Fine-tuned model support

---

# Summary

The Model Gateway provides a scalable and provider-independent foundation for integrating multiple AI models into the evaluation platform.
