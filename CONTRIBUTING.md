# Contributing to AI Logging Intelligence

Thank you for considering contributing to AI Logging Intelligence! 🎉

## 🌟 Ways to Contribute

### 1. Report Bugs
Found a bug? Please [open an issue](https://github.com/yourusername/ai-logging-intelligence/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)

### 2. Suggest Features
Have an idea? [Start a discussion](https://github.com/yourusername/ai-logging-intelligence/discussions) or open an issue labeled "enhancement"

### 3. Improve Documentation
- Fix typos or unclear explanations
- Add examples or tutorials
- Improve API documentation
- Write blog posts or guides

### 4. Submit Code
- Fix bugs
- Implement new features
- Improve performance
- Add tests

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- (Optional) OpenAI API key for testing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-logging-intelligence
   cd ai-logging-intelligence
   ```

2. **Set Up Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -e ".[dev]"
   ```

3. **Start Services**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d db redis
   
   # Run migrations
   alembic upgrade head
   
   # Start API service
   uvicorn src.main:app --reload
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

---

## 📝 Development Workflow

### Branch Naming
- `feat/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add anomaly detection to pattern analyzer
fix: handle edge case in log signature generation
docs: update API reference for policy endpoints
test: add integration tests for PostHog client
```

### Code Style

**Python:**
- Use `ruff` for linting: `ruff check . --fix`
- Use `ruff` for formatting: `ruff format .`
- Add type hints everywhere
- Follow PEP 8 (120 char line length)
- Write docstrings for all functions

**JavaScript/TypeScript:**
- Use `eslint` and `prettier`
- Add JSDoc comments
- Use strict TypeScript settings

### Testing
- Write tests for all new features
- Maintain > 80% code coverage
- Include unit and integration tests
- Test error cases and edge conditions

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_pattern_analyzer.py::test_clustering

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## 🔄 Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation
   - Run linters and tests

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

4. **Push to Fork**
   ```bash
   git push origin feat/your-feature-name
   ```

5. **Open Pull Request**
   - Go to GitHub and create a PR
   - Fill out the PR template
   - Link related issues
   - Request review

### PR Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commit messages are clear
- [ ] PR description explains changes

---

## 🧪 Testing Guidelines

### Unit Tests
- Test individual functions/classes
- Mock external dependencies
- Fast execution (< 1s per test)

```python
def test_pattern_signature_generation():
    analyzer = PatternAnalyzer()
    sig1 = analyzer.compute_signature("User 123 logged in")
    sig2 = analyzer.compute_signature("User 456 logged in")
    assert sig1 == sig2  # Should be same pattern
```

### Integration Tests
- Test component interactions
- Use real databases (test containers)
- Test API endpoints end-to-end

```python
def test_policy_generation_flow(client, db):
    # Send logs
    response = client.post("/api/v1/patterns/analyze", json={...})
    
    # Verify policy generated
    policy = client.get("/api/v1/policies/my-service")
    assert policy["global_rate"] < 1.0
```

### Performance Tests
- Benchmark critical paths
- Ensure no regressions
- Document expected performance

---

## 📚 Documentation

### Code Documentation
- Add docstrings to all public functions
- Include examples in docstrings
- Document parameters and return types

```python
def cluster_patterns(self, logs: List[Log]) -> List[Cluster]:
    """
    Cluster similar log messages using DBSCAN.
    
    Args:
        logs: List of log entries to cluster
        
    Returns:
        List of clusters with metadata
        
    Example:
        >>> analyzer = PatternAnalyzer()
        >>> clusters = analyzer.cluster_patterns(logs)
        >>> print(f"Found {len(clusters)} clusters")
    """
    ...
```

### User Documentation
- Update README.md for user-facing changes
- Add examples to `/examples`
- Update API docs in `/docs`

---

## 🤔 Questions?

- **General questions:** [GitHub Discussions](https://github.com/yourusername/ai-logging-intelligence/discussions)
- **Bug reports:** [GitHub Issues](https://github.com/yourusername/ai-logging-intelligence/issues)
- **Security issues:** Email security@example.com (private)
- **Other:** your.email@example.com

---

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

---

## 🎉 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Given credit in documentation

---

Thank you for contributing! 🙏

