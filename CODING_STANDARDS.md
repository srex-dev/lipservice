# 🎯 LipService Coding Standards

**Aligned with PostHog's Standards - October 9, 2025**

---

## 🎯 Core Principle

**Match PostHog's coding standards exactly** to ensure:
- Easy contribution to PostHog
- Familiar codebase for PostHog engineers
- Consistent dependency versions
- Smooth integration path

---

## 🐍 Python Standards

### **Version**
```toml
requires-python = "==3.11.*"  # Exactly match PostHog
```

**Why:** PostHog uses Python 3.11 exactly, not 3.11+

### **Ruff Configuration**
```toml
line-length = 120  # PostHog standard
target-version = "py311"
```

### **Ruff Rules (Match PostHog Exactly)**
```toml
select = [
    "B",       # flake8-bugbear
    "C4",      # flake8-comprehensions
    "C9",      # mccabe
    "E",       # pycodestyle errors
    "F",       # pyflakes
    "I",       # isort
    "RUF005",  # collection-literal-concatenation
    "RUF013",  # implicit-optional
    "RUF015",  # unnecessary-iterable-allocation
    "RUF019",  # unnecessary-key-check
    "T100",    # debugger
    "T2",      # print-found
    "TRY201",  # verbose-raise
    "TRY400",  # error-instead-of-exception
    "UP",      # pyupgrade
    "W",       # pycodestyle warnings
]

ignore = [
    "B017", "B019", "B904", "B905",
    "C901", "E501", "E722", "E731",
    "F403", "F541", "F601",
    "UP007", "UP032",
]
```

### **Import Ordering (isort)**
```python
# Standard library
import os
import sys

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local
from src.engine import PatternAnalyzer
from src.storage import models
```

**Config:**
```toml
combine-as-imports = true
force-wrap-aliases = true
length-sort-straight = true
split-on-trailing-comma = false
```

### **Code Formatting**
```python
# Double quotes (not single)
message = "Hello world"

# 4-space indentation
def my_function():
    if condition:
        do_something()

# Line length: 120 characters max
very_long_function_call(argument1, argument2, argument3, argument4)  # Max 120 chars

# Type hints everywhere
def process_logs(logs: list[LogEntry]) -> PatternAnalysis:
    ...
```

---

## 📦 Dependency Management

### **Key Principle: Match PostHog Versions Exactly**

```toml
# ✅ CORRECT (PostHog's exact versions)
"redis==4.5.4"           # Not 6.x!
"openai==1.102.0"        # Exact match
"anthropic==0.52.0"      # Exact match
"sqlalchemy==2.0.38"     # Exact match
"pydantic==2.10.3"       # Close match (PostHog uses 2.10.3, we use 2.10.5)
"structlog==25.4.0"      # Exact match
"scikit-learn==1.5.0"    # Exact match
"numpy==1.26.4"          # Exact match

# OpenTelemetry (for OTLP exporters)
"opentelemetry-sdk==1.33.1"                    # PostHog's version
"opentelemetry-exporter-otlp-proto-grpc==1.33.1"  # PostHog's version
```

### **Why This Matters:**
- Compatible with PostHog's production environment
- Same tested dependency versions
- Easier to contribute code to PostHog
- No version conflicts if integrated

---

## 🧪 Testing Standards

### **Framework**
```python
import pytest
import pytest-asyncio  # For async tests
import pytest-cov      # For coverage

# PostHog uses pytest 8.0.2
```

### **Test Structure**
```python
# test_module.py

def test_function_does_something():
    """Test description in docstring."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output


@pytest.mark.asyncio
async def test_async_function():
    """Test async functions."""
    result = await async_function()
    assert result is not None
```

### **Coverage Target**
```toml
# Minimum 80%, target 95%+
[tool.pytest.ini_options]
addopts = [
    "-v",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
]
```

---

## 📝 Documentation Standards

### **Docstrings (Google Style)**
```python
def analyze_patterns(logs: list[LogEntry], threshold: float = 0.5) -> PatternAnalysis:
    """
    Analyze log patterns using ML clustering.
    
    Args:
        logs: List of log entries to analyze
        threshold: Clustering distance threshold (default: 0.5)
        
    Returns:
        PatternAnalysis with clusters and statistics
        
    Raises:
        ValueError: If logs list is None
        
    Example:
        >>> logs = [LogEntry("User logged in", "INFO", ...)]
        >>> result = analyze_patterns(logs)
        >>> print(result.total_unique_patterns)
        15
    """
    ...
```

### **Code Comments**
```python
# Use comments for "why", not "what"

# ✅ GOOD
# Cache this result because DB queries are expensive
result = cache.get_or_compute(key, expensive_query)

# ❌ BAD
# Get result from cache or compute
result = cache.get_or_compute(key, expensive_query)
```

---

## 🏗️ Architecture Standards

### **File Organization (Match PostHog)**
```
src/
├── api/              # FastAPI routers (like PostHog's)
├── engine/           # Core logic (analysis, ML)
├── integrations/     # External integrations (PostHog, etc.)
├── storage/          # Database models (SQLAlchemy)
└── utils/            # Shared utilities

tests/
├── conftest.py       # Pytest fixtures
├── test_*.py         # Unit tests
└── integration/      # Integration tests
```

### **Module Design**
```python
# One clear responsibility per module
# signature.py - ONLY signature generation
# sampler.py - ONLY sampling logic
# client.py - ONLY API communication

# No god classes or files >500 lines
```

---

## 🔐 Security Standards

### **Secrets Management**
```python
# ✅ CORRECT
import os
api_key = os.getenv("OPENAI_API_KEY")

# ❌ WRONG
api_key = "sk-..."  # Never hardcode!
```

### **Input Validation**
```python
# Always use Pydantic for validation
from pydantic import BaseModel, Field

class PolicyRequest(BaseModel):
    team_id: int = Field(gt=0)  # Must be positive
    hours: int = Field(ge=1, le=168)  # 1-168 hours
```

---

## 📊 OpenTelemetry Standards

### **Protocol Compliance**
```python
# Use OpenTelemetry SDK (PostHog's versions)
from opentelemetry.sdk import _logs
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

# Follow OTLP spec exactly
# PostHog's Rust service expects standard OTLP format
```

### **Attributes Mapping**
```python
# Match PostHog's schema (from products/logs/backend/schema.sql)
log_record = {
    "timestamp": datetime.now(),
    "severity_text": "INFO",
    "severity_number": 9,  # OTLP standard
    "body": "Log message",
    "attributes": {...},  # JSON format
    "resource_attributes": {...},
    "trace_id": "...",
    "span_id": "...",
}
```

---

## 🎯 SDK Standards (For All Languages)

### **API Consistency**
```python
# Python
configure_adaptive_logging(
    service_name="my-app",
    lipservice_url="...",
    posthog_api_key="phc_xxx",
)

# JavaScript (should be similar)
configureAdaptiveLogging({
    serviceName: "my-app",
    lipserviceUrl: "...",
    posthogApiKey: "phc_xxx",
})

# Go (should be similar)
lipservice.Configure(lipservice.Config{
    ServiceName: "my-app",
    LipServiceURL: "...",
    PostHogAPIKey: "phc_xxx",
})
```

### **Error Handling**
```python
# Always graceful degradation
try:
    policy = await fetch_policy()
except Exception as e:
    logger.error("policy_fetch_failed", error=str(e))
    policy = get_fallback_policy()  # Never crash!
```

### **Performance Requirements**
- Sampling decision: < 1ms
- Policy fetch: < 100ms
- Pattern reporting: < 500ms
- Memory: < 50MB per SDK instance

---

## 📋 Checklist for New Code

Before committing, verify:

- [ ] **Ruff passes:** `ruff check .`
- [ ] **Tests pass:** `pytest tests/ -v`
- [ ] **Coverage >80%:** `pytest --cov=src`
- [ ] **Type hints:** All functions have type annotations
- [ ] **Docstrings:** All public functions documented
- [ ] **No hardcoded secrets:** Use environment variables
- [ ] **Dependencies match PostHog:** Check `pyproject.toml`
- [ ] **Line length ≤120:** Ruff will enforce
- [ ] **Imports sorted:** isort-compliant
- [ ] **No print statements:** Use `logger` instead
- [ ] **Error handling:** Graceful degradation
- [ ] **OpenTelemetry compliance:** If building OTLP features

---

## 🔄 Version Alignment

| Dependency | PostHog Version | LipService Version | Status |
|------------|----------------|-------------------|---------|
| **Python** | ==3.11.* | ==3.11.* | ✅ Match |
| **redis** | 4.5.4 | 4.5.4 | ✅ Match |
| **openai** | 1.102.0 | 1.102.0 | ✅ Match |
| **anthropic** | 0.52.0 | 0.52.0 | ✅ Match |
| **sqlalchemy** | 2.0.38 | 2.0.38 | ✅ Match |
| **pydantic** | 2.10.3 | 2.10.5 | ⚠️ Close |
| **structlog** | 25.4.0 | 25.4.0 | ✅ Match |
| **scikit-learn** | 1.5.0 | 1.5.0 | ✅ Match |
| **numpy** | 1.26.4 | 1.26.4 | ✅ Match |
| **opentelemetry-sdk** | 1.33.1 | 1.33.1 | ✅ Match |
| **ruff** | ~0.8.1 | >=0.8.6 | ✅ Compatible |

---

## 🚀 SDK-Specific Standards

### **Python SDK (`sdk/python/`)**
- Match backend standards
- Same ruff/mypy config
- Python 3.11+
- Type hints required

### **TypeScript SDK (`sdk/typescript/`) - Coming Sprint 7**
```typescript
// Use ESLint + Prettier
// Match PostHog's frontend standards
// TypeScript strict mode
// 120 character line length
```

### **Go SDK (`sdk/go/`) - Optional Sprint 9**
```go
// Use gofmt + golangci-lint
// Follow Go standard project layout
// Full test coverage
```

---

## 📚 Documentation Standards

### **README Structure**
1. One-line value proposition
2. Quick example (copy-paste ready)
3. Installation
4. Usage
5. API reference
6. Contributing
7. License

### **Code Examples**
```python
# Always provide working, copy-paste ready examples
# Include imports
# Include expected output
# Keep it simple

from lipservice import configure_adaptive_logging

configure_adaptive_logging(
    service_name="my-app",
    lipservice_url="https://lipservice.com"
)
# That's it! Logs are now intelligently sampled.
```

---

## 🔄 Continuous Alignment

### **Stay Updated with PostHog**
- [ ] Monitor PostHog's pyproject.toml for dependency updates
- [ ] Check PostHog PRs for coding standard changes
- [ ] Review PostHog's ruff/mypy configs quarterly
- [ ] Update our standards to match

### **When PostHog Changes**
1. Update our `pyproject.toml`
2. Run `ruff check . --fix`
3. Run tests
4. Update this document

---

## ✅ Pre-Commit Checklist

Every commit should:
- [ ] Pass `ruff check .`
- [ ] Pass `ruff format .`
- [ ] Pass `pytest tests/`
- [ ] Have no print() statements (use logger)
- [ ] Have type hints
- [ ] Have docstrings
- [ ] Match PostHog dependency versions

---

## 🎯 Why This Matters

1. **Contribution Ready:** Code can be contributed to PostHog without refactoring
2. **Familiar to PostHog Team:** They recognize the patterns
3. **Production Proven:** PostHog's standards are battle-tested
4. **Integration Smooth:** No version conflicts
5. **Professional:** Shows we're serious about collaboration

---

**Last Updated:** October 9, 2025  
**Review Schedule:** Every sprint or when PostHog updates standards
