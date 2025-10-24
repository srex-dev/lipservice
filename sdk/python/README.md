# 🎙️ LipService Python SDK

> **Reduce logging costs by 50-80% with AI-powered intelligent sampling + PostHog integration**

[![PyPI](https://img.shields.io/pypi/v/lipservice-sdk)](https://pypi.org/project/lipservice-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/lipservice-sdk)](https://pypi.org/project/lipservice-sdk/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 🌟 What is LipService SDK?

LipService SDK enables **intelligent, AI-powered log sampling** in your Python applications with **built-in PostHog integration**. It automatically:

- ✅ **Keeps 100% of errors and critical logs** (never lose important data)
- ✅ **Samples repetitive logs at 1-20%** (reduce noise and cost)
- ✅ **Boosts sampling during anomalies** (catch issues early)
- ✅ **Adapts policies automatically** (AI learns your patterns)
- ✅ **Reduces log costs by 50-80%** (while maintaining observability)
- ✅ **Direct PostHog integration** (one-line setup with OTLP)

---

## 🚀 Quick Start

### Installation

```bash
pip install lipservice-sdk
```

### Basic Usage

```python
from lipservice import configure_adaptive_logging, get_logger

# One-line configuration
configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com"
)

# Use logging as normal - AI handles sampling!
logger = get_logger(__name__)

logger.info("user_login", user_id=123)  # Sampled intelligently
logger.error("payment_failed", amount=99.99)  # Always kept (100%)
```

### PostHog Integration (NEW!)

```python
from lipservice import configure_adaptive_logging, get_logger

# One-line PostHog integration
configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    posthog_api_key="phc_xxx",  # Your PostHog API key
    posthog_team_id="12345",    # Your PostHog team ID
)

# Logs are intelligently sampled AND sent to PostHog automatically!
logger = get_logger(__name__)
logger.info("user_login", user_id=123)  # Sampled + sent to PostHog
logger.error("payment_failed", amount=99.99)  # Always kept + sent to PostHog
```

**That's it!** Your logs are now intelligently sampled and sent directly to PostHog.

---

## 📖 How It Works

```
Your Application
      ↓
   LipService SDK
   ├── Detect patterns in logs
   ├── Fetch AI sampling policy
   ├── Make sampling decisions
   └── Send sampled logs
      ↓
   PostHog / Log Storage
   (50-80% reduced volume!)
```

### Example: Before vs After

**Without LipService:**
```
1,000,000 logs/day → PostHog → $500/month
```

**With LipService:**
```
1,000,000 logs/day
   ↓ AI sampling (DEBUG: 5%, INFO: 20%, ERROR: 100%)
200,000 logs/day → PostHog → $100/month

💰 Savings: $400/month (80% reduction)
```

---

## 🎯 Features

### 1. **Pattern Detection**
Automatically identifies similar log messages:
```python
logger.info("User 123 logged in")  # Pattern: "User N logged in"
logger.info("User 456 logged in")  # Same pattern!
```

### 2. **Severity-Based Sampling**
Different rates for different log levels:
- `DEBUG`: 5% (minimal noise)
- `INFO`: 20% (relevant signals)
- `WARNING`: 50% (potential issues)
- `ERROR`: 100% (never miss)
- `CRITICAL`: 100% (always capture)

### 3. **AI Policy Generation**
LipService analyzes your logs and generates intelligent policies:
```json
{
  "global_rate": 0.3,
  "severity_rates": {
    "DEBUG": 0.05,
    "INFO": 0.2,
    "ERROR": 1.0
  },
  "pattern_rates": {
    "abc123": 0.01  // Noisy pattern sampled at 1%
  },
  "anomaly_boost": 3.0  // 3x sampling during anomalies
}
```

### 4. **Automatic Policy Updates**
Policies refresh every 5 minutes, adapting to your application's behavior.

### 5. **Pattern Reporting**
SDK reports pattern statistics back to LipService for continuous improvement.

---

## 🎯 PostHog Integration

### Why PostHog + LipService?

- **PostHog provides:** Log storage, querying, and UI
- **LipService adds:** AI-powered intelligent sampling
- **Together:** 50-80% cost reduction with zero data loss

### PostHog Cloud Integration

```python
from lipservice import configure_adaptive_logging, get_logger

configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    posthog_api_key="phc_xxx",  # From PostHog settings
    posthog_team_id="12345",    # From PostHog settings
)

logger = get_logger(__name__)
logger.info("user_action", user_id=123, action="login")
```

### Self-Hosted PostHog Integration

```python
configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    posthog_api_key="phc_xxx",
    posthog_team_id="12345",
    posthog_endpoint="https://posthog.company.com",  # Your self-hosted URL
)
```

### PostHog Features

- ✅ **OTLP Protocol:** Uses OpenTelemetry standard
- ✅ **Batch Export:** Efficient log batching
- ✅ **Retry Logic:** Handles network issues gracefully
- ✅ **Authentication:** JWT-based auth with PostHog
- ✅ **Team Isolation:** Proper team ID handling
- ✅ **Error Handling:** Graceful degradation

---

### Django

```python
# settings.py
LIPSERVICE = {
    'SERVICE_NAME': 'my-django-app',
    'LIPSERVICE_URL': 'https://lipservice.company.com',
    'API_KEY': 'optional-key',
}

# apps.py
from lipservice.integrations.django import configure_lipservice_django

class MyAppConfig(AppConfig):
    def ready(self):
        configure_lipservice_django()
```

### FastAPI

```python
from fastapi import FastAPI
from lipservice.integrations.fastapi import (
    configure_lipservice_fastapi,
    LipServiceMiddleware
)

app = FastAPI()

# Configure
configure_lipservice_fastapi(
    service_name="my-fastapi-app",
    lipservice_url="https://lipservice.company.com"
)

# Add middleware for request context
app.add_middleware(LipServiceMiddleware)
```

### Flask

```python
from flask import Flask
from lipservice.integrations.flask import init_lipservice

app = Flask(__name__)

init_lipservice(
    app,
    service_name="my-flask-app",
    lipservice_url="https://lipservice.company.com"
)
```

---

## 📚 Advanced Usage

### Custom Downstream Handler

Forward sampled logs to your existing log handler:

```python
import logging
from lipservice import configure_adaptive_logging

# Your existing handler (e.g., PostHog, Datadog)
posthog_handler = logging.Handler()  # Your PostHog handler

configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    downstream_handler=posthog_handler  # Forward sampled logs here
)
```

### Structlog Integration

```python
import structlog
from lipservice import configure_adaptive_logging

configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    use_structlog=True
)

logger = structlog.get_logger()
logger.info("user_action", user_id=123, action="login")
```

### Manual Sampler Control

```python
from lipservice.config import get_sampler

sampler = get_sampler()

# Get sampling statistics
stats = sampler.get_stats()
print(f"Policy version: {stats['policy_version']}")
print(f"Patterns tracked: {stats['patterns_tracked']}")

# Force policy refresh
await sampler._refresh_policy()

# Force pattern report
await sampler._report_patterns()
```

### Graceful Shutdown

```python
from lipservice import shutdown

# In your shutdown handler
async def app_shutdown():
    await shutdown()  # Reports final patterns
```

---

## 🔐 Configuration Options

```python
configure_adaptive_logging(
    service_name="my-api",                    # Required: Service identifier
    lipservice_url="https://...",             # Required: LipService API URL
    api_key="optional-key",                   # Optional: API key for auth
    policy_refresh_interval=300,              # Seconds between policy updates
    pattern_report_interval=600,              # Seconds between pattern reports
    downstream_handler=my_handler,            # Optional: Forward sampled logs
    use_structlog=True,                       # Use structlog (default: True)
    max_pattern_cache_size=10000,             # Max patterns to track
    fallback_sample_rate=1.0,                 # Rate when policy unavailable
)
```

---

## 🧪 Testing

### Unit Tests

```bash
cd sdk/python
pytest tests/ -v
```

### With Coverage

```bash
pytest tests/ --cov=lipservice --cov-report=html
```

---

## 📊 Cost Savings Calculator

Estimate your savings:

| Log Volume/Day | Without LipService | With LipService | Savings |
|----------------|-------------------|----------------|---------|
| 100K logs      | $50/month         | $10/month      | **$40 (80%)** |
| 1M logs        | $500/month        | $100/month     | **$400 (80%)** |
| 10M logs       | $5,000/month      | $1,000/month   | **$4,000 (80%)** |

*Assuming typical log distribution (40% DEBUG, 40% INFO, 15% WARN, 5% ERROR)*

---

## 🔍 FAQ

### Q: Will I lose error logs?
**A: No!** ERROR and CRITICAL logs are ALWAYS sampled at 100%.

### Q: How does pattern detection work?
**A:** We normalize messages by replacing variables (IDs, timestamps, numbers) with placeholders, so similar messages get the same signature.

### Q: What if LipService API is down?
**A:** SDK falls back to 100% sampling (configurable) to ensure no data loss.

### Q: Does this work with existing logging setup?
**A:** Yes! LipService wraps your existing logging and forwards sampled logs to your current handlers.

### Q: How often do policies update?
**A:** Every 5 minutes by default (configurable).

---

## 🤝 Support

- **Documentation:** https://lipservice.readthedocs.io
- **Issues:** https://github.com/yourorg/lipservice/issues
- **Discord:** https://discord.gg/lipservice

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built to complement [PostHog](https://posthog.com)'s logging infrastructure with AI-powered cost optimization.

---

**Start saving on logging costs today!** 🚀

```bash
pip install lipservice-sdk
```

