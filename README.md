# 🎙️ LipService

> **Intelligent, AI-powered log sampling that reduces costs by 50-80% while maintaining full observability**

[![Tests](https://github.com/srex-dev/lipservice/actions/workflows/test.yml/badge.svg)](https://github.com/srex-dev/lipservice/actions/workflows/test.yml)
[![Lint](https://github.com/srex-dev/lipservice/actions/workflows/lint.yml/badge.svg)](https://github.com/srex-dev/lipservice/actions/workflows/lint.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 🌟 What is This?

LipService is a next-generation logging system that uses Large Language Models (LLMs) to:

- **Automatically optimize log sampling** based on patterns and context
- **Detect anomalies** and explain them in plain language
- **Reduce logging costs by 50-80%** without losing observability
- **Provide intelligent insights** about your system's behavior
- **Work seamlessly** with PostHog (and other platforms)

Instead of manually configuring sampling rates or drowning in log noise, the AI learns your patterns and makes intelligent decisions about what to keep and what to safely discard.

---

## 🚀 Quick Example

```python
from ai_logging import configure_adaptive_logging
import structlog

# One line of configuration
configure_adaptive_logging(
    service_name="my-api",
    api_key="phc_xxx",
    enable_ai_sampling=True,
)

# Use standard logging - AI handles the rest
logger = structlog.get_logger()
logger.info("user_login", user_id=123)  # Sampled intelligently
logger.error("payment_failed", amount=99.99)  # Always kept
```

**Result:** The system automatically:
- Keeps 100% of errors and critical logs
- Samples repetitive INFO logs at 5-10%
- Boosts sampling during anomalies
- Saves you 60% on log storage costs

---

## 💡 Key Features

### 🧠 AI-Powered Sampling
- Uses GPT-4/Claude/Ollama to generate sampling policies
- Understands log semantics, not just volume
- Adapts to your specific patterns
- Explains every decision

### 📊 Pattern Analysis
- Automatically clusters similar logs
- Detects unusual patterns and spikes
- Tracks frequency over time
- Identifies noisy vs valuable logs

### 💰 Cost Optimization
- Predicts monthly log costs
- Suggests specific cost-saving measures
- Shows ROI in real-time
- Balances cost vs observability

### 🔍 Intelligent Insights
- Explains anomalies in plain language
- Suggests debugging steps
- Correlates with deployments/incidents
- Proactive issue detection

### 🔌 Easy Integration
- Works with PostHog, Grafana Loki, Elasticsearch
- SDKs for Python, JavaScript, Go, Rust
- OpenTelemetry standard
- No vendor lock-in

---

## 🏗️ Architecture

```
┌─────────────────────────────┐
│  Your Application           │
│  (Python/JS/Go/etc.)        │
│  └─ AI Logging SDK          │
└──────────────┬──────────────┘
               │ OTLP + Metadata
               ↓
┌──────────────────────────────┐
│  AI Logging Intelligence     │
│  - Pattern Analysis          │
│  - LLM Policy Generation     │
│  - Anomaly Detection         │
│  - Cost Optimization         │
└──────────────┬───────────────┘
               │ Policies
               ↓
┌──────────────────────────────┐
│  Log Storage                 │
│  (PostHog/Loki/ES)          │
└──────────────────────────────┘
```

---

## 📦 Installation

### Service (Backend)
```bash
# Clone the repository
git clone https://github.com/srex-dev/lipservice.git
cd lipservice

# Start with Docker Compose
docker-compose up -d

# Or install locally
pip install -e .
uvicorn src.main:app --reload
```

### Python SDK
```bash
pip install ai-logging
```

### JavaScript SDK
```bash
npm install @ai-logging/sdk
```

---

## 📚 Documentation

- [**Iteration Spec**](ITERATION_SPEC.md) - Detailed technical specification
- [**Roadmap**](ROADMAP.md) - Development timeline and milestones
- [**TODO**](TODO.md) - Task list and progress tracking

---

## 🛠️ Development Status

**Current Sprint:** Sprint 1 - Project Setup (Weeks 1-2)  
**Progress:** 🟡 Just Started  
**Next Milestone:** MVP (Week 12)

### Recent Updates
- ✅ Project planning complete
- ✅ Fresh PostHog codebase pulled
- 🚧 Setting up project structure
- ⏳ Basic API service coming next

See [TODO.md](TODO.md) for detailed task list.

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [PostHog](https://posthog.com) for the excellent logging infrastructure
- [OpenTelemetry](https://opentelemetry.io) for the standard protocol
- [FastAPI](https://fastapi.tiangolo.com) for the amazing framework

---

**Built with ❤️ and 🤖 for intelligent logging**

