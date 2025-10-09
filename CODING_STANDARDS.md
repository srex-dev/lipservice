# Coding Standards - LipService

**Aligned with PostHog's coding standards for easy contribution**

---

## 🎯 Philosophy

From PostHog's AGENTS.md:
- **Start simple, iterate:** Build minimal solution first, add complexity only when demanded
- **Avoid over-engineering:** Don't apply design patterns just because you know them
- **Reduce nesting:** Use early returns, guard clauses, and helper methods
- **Separation of concerns:** Keep different responsibilities in different places
- **Balance simplicity and maintainability:** Tension between fewest parts and understandable code

---

## 🐍 Python Standards

### General
- **Python version:** 3.11+
- **Line length:** 120 characters (PostHog standard, not PEP 8's 79)
- **Naming:** `snake_case` for variables and functions
- **Type hints:** Use everywhere (follow mypy strict rules)
- **Imports:** Organize with isort (automatically via ruff)
- **Spelling:** American English

### Type Hints (Required)
```python
# ✅ Good
def fetch_logs(team_id: int, limit: int = 1000) -> list[Log]:
    return []

async def analyze_patterns(logs: list[Log]) -> PatternAnalysis:
    ...

# ❌ Bad (no type hints)
def fetch_logs(team_id, limit=1000):
    return []
```

### Error Handling
```python
# ✅ Good - explicit, typed errors
class PatternAnalysisError(Exception):
    """Raised when pattern analysis fails."""
    pass

def analyze(logs: list[Log]) -> Analysis:
    if not logs:
        raise PatternAnalysisError("No logs provided")
    try:
        return compute_patterns(logs)
    except ValueError as e:
        raise PatternAnalysisError(f"Invalid log format: {e}") from e

# ❌ Bad - bare except
def analyze(logs):
    try:
        return compute_patterns(logs)
    except:
        return None
```

### Early Returns (Reduce Nesting)
```python
# ✅ Good - early returns, flat structure
def process_log(log: Log) -> ProcessedLog | None:
    if not log:
        return None
    
    if not log.is_valid():
        logger.warning("Invalid log", log_id=log.id)
        return None
    
    if log.team_id not in active_teams:
        return None
    
    return ProcessedLog(log)

# ❌ Bad - deeply nested
def process_log(log):
    if log:
        if log.is_valid():
            if log.team_id in active_teams:
                return ProcessedLog(log)
            else:
                return None
        else:
            logger.warning("Invalid log")
            return None
    else:
        return None
```

---

## 📝 Comments

From PostHog standards:
> **Comments should not duplicate the code below.** Don't tell me "this finds the shortest username" tell me _why_ that is important. If it isn't important, don't add a comment. **Almost never add a comment.**

```python
# ✅ Good - explains WHY
def cluster_patterns(logs: list[Log], eps: float = 0.5) -> list[Cluster]:
    # We use eps=0.5 because testing showed it balances precision/recall
    # for typical log message variations (typos, different IDs, etc)
    return DBSCAN(eps=eps).fit(logs)

# ❌ Bad - duplicates what code does
def cluster_patterns(logs: list[Log]) -> list[Cluster]:
    # This function clusters the patterns using DBSCAN
    return DBSCAN(eps=0.5).fit(logs)

# ✅ Best - no comment needed if code is clear
def cluster_similar_logs(logs: list[Log]) -> list[Cluster]:
    return DBSCAN(eps=0.5, min_samples=2).fit(logs)
```

---

## 🧪 Testing Standards

### Use Pytest
```python
# ✅ Good
def test_pattern_clustering_groups_similar_logs():
    logs = [
        Log("User 123 logged in"),
        Log("User 456 logged in"),
        Log("Payment failed"),
    ]
    
    clusters = cluster_patterns(logs)
    
    assert len(clusters) == 2
    assert clusters[0].contains(logs[0]) and clusters[0].contains(logs[1])

# ❌ Bad - no doc comments in tests (PostHog rule)
def test_pattern_clustering():
    """
    This test checks that pattern clustering works correctly
    by grouping similar logs together.
    """
    ...
```

### Parameterized Tests
From PostHog standards:
> **Every time you are tempted to add more than one assertion to a test, consider (really carefully) if it should be a parameterized test instead.**

```python
# ✅ Good - parameterized
import pytest

@pytest.mark.parametrize("log_message,expected_signature", [
    ("User 123 logged in", "user_n_logged_in"),
    ("User 456 logged in", "user_n_logged_in"),
    ("Payment $99.99 failed", "payment_n_failed"),
    ("Payment $49.99 failed", "payment_n_failed"),
])
def test_log_signature_generation(log_message: str, expected_signature: str):
    signature = compute_signature(log_message)
    assert signature == expected_signature

# ❌ Bad - multiple assertions for similar cases
def test_log_signature_generation():
    assert compute_signature("User 123 logged in") == "user_n_logged_in"
    assert compute_signature("User 456 logged in") == "user_n_logged_in"
    assert compute_signature("Payment $99.99 failed") == "payment_n_failed"
    assert compute_signature("Payment $49.99 failed") == "payment_n_failed"
```

---

## 🛠️ Tools & Commands

### Linting & Formatting
```bash
# Format code (do this often!)
ruff format .

# Check for issues
ruff check .

# Fix auto-fixable issues
ruff check . --fix

# Type checking (slow, don't run often)
mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_pattern_analyzer.py::test_clustering

# Run with coverage
pytest --cov=src --cov-report=html

# Run fast (skip slow tests)
pytest -m "not slow"
```

### Pre-commit Checklist
Before committing:
1. ✅ `ruff format .` - format code
2. ✅ `ruff check . --fix` - fix linting issues
3. ✅ `pytest` - run tests
4. ✅ Review changes manually
5. ✅ Write clear commit message

---

## 📦 Project Structure

Follow PostHog's separation of concerns:

```
src/
├── api/              # REST API endpoints (presentation layer)
├── engine/           # Core business logic (pattern analysis, LLM)
├── storage/          # Database models and queries (data layer)
├── integrations/     # External services (PostHog, OpenAI)
└── utils/            # Shared utilities
```

### Module Organization
```python
# ✅ Good - clear separation
# src/engine/pattern_analyzer.py
class PatternAnalyzer:
    """Core business logic for pattern analysis."""
    def cluster_patterns(self, logs: list[Log]) -> list[Cluster]:
        ...

# src/api/patterns.py
@router.post("/patterns/analyze")
async def analyze_patterns(request: AnalyzeRequest) -> AnalyzeResponse:
    """API endpoint - thin layer over business logic."""
    analyzer = PatternAnalyzer()
    result = analyzer.cluster_patterns(request.logs)
    return AnalyzeResponse.from_analysis(result)

# src/storage/models.py
class Pattern(Base):
    """Database model - just data."""
    __tablename__ = "patterns"
    id: Mapped[int] = mapped_column(primary_key=True)
```

---

## 🎨 Code Style Examples

### Good Examples from PostHog Philosophy

```python
# ✅ Descriptive names
def compute_log_signature(message: str) -> str:
    """Generate a normalized signature for log message clustering."""
    normalized = remove_variable_parts(message)
    return hashlib.md5(normalized.encode()).hexdigest()

# ✅ Early returns, flat structure
async def generate_policy(patterns: list[Pattern]) -> Policy:
    if not patterns:
        return Policy.default()
    
    if len(patterns) < MIN_PATTERNS_FOR_AI:
        logger.info("Too few patterns, using rule-based policy")
        return Policy.from_rules(patterns)
    
    try:
        return await llm.generate_policy(patterns)
    except LLMError as e:
        logger.error("LLM failed, falling back", error=str(e))
        return Policy.from_rules(patterns)

# ✅ Type hints with modern syntax
def fetch_logs(
    team_id: int,
    time_range: TimeRange,
    service_name: str | None = None,
) -> list[Log]:
    ...
```

---

## 🚫 Anti-Patterns to Avoid

```python
# ❌ Over-engineering
class AbstractPatternAnalyzerFactoryInterface:
    """Don't create abstractions until you need them!"""
    ...

# ❌ Deeply nested code
def process(log):
    if log:
        if log.valid:
            if log.team_id:
                if log.message:
                    return analyze(log)

# ❌ No type hints
def analyze(logs):
    return compute_patterns(logs)

# ❌ Bare exceptions
try:
    risky_operation()
except:
    pass

# ❌ Magic numbers
if len(logs) > 42:  # What is 42?
    ...
```

---

## 📚 References

- [PostHog AGENTS.md](https://github.com/PostHog/posthog/blob/master/AGENTS.md)
- [PostHog CODE_REVIEW.md](https://github.com/PostHog/posthog/blob/master/CODE_REVIEW.md)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)

---

## 🎯 TL;DR

1. **Use type hints everywhere**
2. **Line length: 120 chars**
3. **Format with `ruff format .`**
4. **Early returns, reduce nesting**
5. **Start simple, iterate**
6. **Comments explain WHY, not WHAT**
7. **Parameterized tests over multiple assertions**
8. **Descriptive names (snake_case in Python)**
9. **Explicit error handling**
10. **Avoid over-engineering**

**Remember:** We're aligning with PostHog to make future contributions easy! 🚀

