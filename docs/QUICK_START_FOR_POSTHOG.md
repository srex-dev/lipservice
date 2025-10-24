# 🚀 Quick Start for PostHog Team

Fast track to testing LipService with your infrastructure.

---

## ⚡ 5-Minute Test

### 1. Clone & Start Backend
```bash
git clone https://github.com/yourorg/lipservice
cd lipservice

# Start services
docker-compose up -d db redis

# Start backend
python src/main.py
# → Running on http://localhost:8000
```

### 2. Install Python SDK
```bash
cd sdk/python
pip install -e .
```

### 3. Run Integration Test
```bash
# Mock data test (works immediately)
python tests/integration/test_posthog_integration.py

# Expected: 50-80% cost reduction shown
```

**Done!** You've seen LipService work in 5 minutes.

---

## 🧪 Test with Real PostHog Data

### Prerequisites
- PostHog running with logs in ClickHouse
- ClickHouse accessible at localhost:9000 (or configure)

### Run Real Data Test
```bash
python tests/integration/test_with_real_posthog_logs.py \
    --clickhouse-host localhost:9000 \
    --team-id 1 \
    --hours 1
```

**Output:**
- Fetches your real logs
- Shows actual pattern detection
- Calculates real cost savings
- Validates with production data

---

## 📊 Generate AI Policy from Your Logs

### Using Rule-Based (No LLM)
```bash
curl -X POST http://localhost:8000/api/v1/pipeline/generate-policy \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": 1,
    "service_name": "posthog-test",
    "hours": 1,
    "clickhouse_host": "localhost:9000",
    "llm_provider": "rule-based"
  }'
```

### Using OpenAI (If You Have API Key)
```bash
export OPENAI_API_KEY="sk-..."

curl -X POST http://localhost:8000/api/v1/pipeline/generate-policy \
  -d '{
    "team_id": 1,
    "service_name": "posthog-test",
    "hours": 1,
    "clickhouse_host": "localhost:9000",
    "llm_provider": "openai"
  }'
```

**Response:** AI-generated sampling policy with reasoning!

---

## 🐍 Try the Python SDK

### Minimal Example
```python
from lipservice import configure_adaptive_logging, get_logger

# Configure (one line!)
configure_adaptive_logging(
    service_name="test-app",
    lipservice_url="http://localhost:8000"
)

# Use normal logging
logger = get_logger(__name__)
logger.info("User action")      # Sampled at ~20%
logger.error("Something broke")  # Always kept (100%)
```

### FastAPI Integration
```python
from fastapi import FastAPI
from lipservice.integrations.fastapi import (
    configure_lipservice_fastapi,
    LipServiceMiddleware
)

app = FastAPI()

configure_lipservice_fastapi(
    service_name="api",
    lipservice_url="http://localhost:8000"
)

app.add_middleware(LipServiceMiddleware)

# All logs automatically sampled!
```

---

## 🔍 Explore the APIs

### Health Check
```bash
curl http://localhost:8000/health
# → {"status":"healthy"}
```

### Query Logs Analysis
```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -d '{
    "team_id": 1,
    "service_name": "test",
    "hours": 1,
    "clickhouse_host": "localhost:9000"
  }'
# → Pattern analysis results
```

### Get Active Policy
```bash
curl http://localhost:8000/api/v1/policies/test-service
# → Current sampling policy
```

---

## 📊 See Cost Savings

Run the mock test to see savings visualization:
```bash
python tests/integration/test_posthog_integration.py
```

**Example Output:**
```
💰 Cost Analysis (based on 263 logs/hour):

   Without LipService:
   - Logs stored: 263 logs/hour
   - Monthly cost: $0.03

   With LipService:
   - Logs stored: 45 logs/hour (17.1%)
   - Monthly cost: $0.01

   💰 Savings:
   - Reduction: 82.9%
   - Monthly savings: $0.02
   - Annual savings: $0.24
```

Scale this to your log volume! 📈

---

## 🏗️ Architecture Overview

```
Your PostHog Logs → LipService Analysis → AI Policy
                          ↓
        SDK Applies Policy → Sampled Logs → PostHog
```

**Key Components:**
1. **Backend API:** Analyzes patterns, generates policies
2. **Python SDK:** Applies sampling in your app
3. **PostHog Integration:** Fetches logs for analysis

---

## 📚 Documentation

- **Project Summary:** `PROJECT_SUMMARY.md` (start here!)
- **Alignment Review:** `docs/POSTHOG_ALIGNMENT_REVIEW.md`
- **Sprint Summaries:** `docs/SPRINT_*_COMPLETE.md`
- **SDK Docs:** `sdk/python/README.md`
- **Integration Guide:** `tests/integration/README.md`

---

## 🐛 Troubleshooting

### "Connection refused" on localhost:8000
**Fix:** Start backend
```bash
python src/main.py
```

### "No logs found in PostHog"
**Fix:** Use mock test first
```bash
python tests/integration/test_posthog_integration.py
```

### "Module not found"
**Fix:** Install SDK
```bash
cd sdk/python && pip install -e .
```

---

## ❓ Questions?

Check these docs:
- `PROJECT_SUMMARY.md` - Overview
- `CONTRIBUTING_TO_POSTHOG.md` - Integration paths
- `docs/POSTHOG_ALIGNMENT_REVIEW.md` - Detailed alignment

Or reach out! We're happy to discuss integration. 🤝

---

## 🎯 Next Steps

After testing:
1. **Feedback:** What works? What needs improvement?
2. **Integration:** Discuss App vs Core integration
3. **Testing:** Test with your production data
4. **Launch:** Plan rollout strategy

---

**Let's reduce logging costs together!** 🚀

