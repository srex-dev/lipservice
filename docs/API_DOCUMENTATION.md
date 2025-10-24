# 📚 LipService API Documentation

## Overview

LipService provides AI-powered intelligent log sampling with PostHog integration. This documentation covers the complete API reference for all SDKs and components.

---

## 🐍 Python SDK API

### Core Functions

#### `configure_adaptive_logging()`

Configure LipService for your application.

```python
from lipservice import configure_adaptive_logging

configure_adaptive_logging(
    service_name: str,
    lipservice_url: str,
    api_key: str | None = None,
    policy_refresh_interval: int = 300,
    pattern_report_interval: int = 600,
    downstream_handler: logging.Handler | None = None,
    use_structlog: bool = True,
    # PostHog integration
    posthog_api_key: str | None = None,
    posthog_team_id: str | None = None,
    posthog_endpoint: str = "https://app.posthog.com",
    **kwargs: Any,
) -> None
```

**Parameters:**
- `service_name` (str): Name of your service
- `lipservice_url` (str): URL of the LipService backend
- `api_key` (str, optional): LipService API key
- `policy_refresh_interval` (int): Seconds between policy refreshes (default: 300)
- `pattern_report_interval` (int): Seconds between pattern reports (default: 600)
- `downstream_handler` (logging.Handler, optional): Custom logging handler
- `use_structlog` (bool): Use structlog for structured logging (default: True)
- `posthog_api_key` (str, optional): PostHog API key
- `posthog_team_id` (str, optional): PostHog team ID
- `posthog_endpoint` (str): PostHog endpoint (default: "https://app.posthog.com")

**Example:**
```python
configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    posthog_api_key="phc_xxx",
    posthog_team_id="12345",
)
```

#### `get_logger()`

Get a LipService logger instance.

```python
from lipservice import get_logger

logger = get_logger(name: str) -> structlog.BoundLogger
```

**Parameters:**
- `name` (str): Logger name

**Returns:**
- `structlog.BoundLogger`: Configured logger instance

**Example:**
```python
logger = get_logger(__name__)
logger.info("User logged in", user_id=123)
```

#### `shutdown()`

Shutdown LipService and cleanup resources.

```python
from lipservice import shutdown

await shutdown() -> None
```

**Example:**
```python
await shutdown()
```

### Classes

#### `AdaptiveSampler`

Intelligent log sampler that makes sampling decisions based on AI policies.

```python
from lipservice import AdaptiveSampler

sampler = AdaptiveSampler(
    client: LipServiceClient,
    policy_refresh_interval: int = 300,
    pattern_report_interval: int = 600,
    max_pattern_cache_size: int = 10000,
)
```

**Methods:**
- `should_sample(message: str, severity: str) -> bool`: Determine if a log should be sampled
- `get_policy() -> SamplingPolicy | None`: Get current sampling policy
- `get_pattern_stats() -> dict[str, PatternStats]`: Get pattern statistics

#### `PostHogOTLPExporter`

PostHog OTLP exporter for sending logs to PostHog.

```python
from lipservice import PostHogOTLPExporter

exporter = PostHogOTLPExporter(
    config: PostHogConfig,
)
```

**Methods:**
- `export_log(message: str, severity: str, timestamp: datetime, context: LogContext | None, **kwargs: Any) -> None`: Export a single log
- `start() -> None`: Start the exporter
- `stop() -> None`: Stop the exporter

#### `PostHogHandler`

Python logging handler for PostHog integration.

```python
from lipservice import PostHogHandler

handler = PostHogHandler(
    config: PostHogConfig,
    level: int = logging.NOTSET,
)
```

**Methods:**
- `emit(record: logging.LogRecord) -> None`: Emit log record to PostHog
- `close() -> None`: Close handler and flush remaining logs

### Performance Module

#### `LRUSignatureCache`

Thread-safe LRU cache for log signatures.

```python
from lipservice.performance import LRUSignatureCache

cache = LRUSignatureCache(
    max_size: int = 10000,
    max_memory_mb: int = 50,
)
```

**Methods:**
- `get(message: str) -> str | None`: Get signature from cache
- `put(message: str, signature: str) -> None`: Put signature in cache
- `get_stats() -> dict[str, Any]`: Get cache statistics
- `clear() -> None`: Clear cache

#### `OptimizedSignatureComputer`

Optimized signature computation with caching.

```python
from lipservice.performance import OptimizedSignatureComputer

computer = OptimizedSignatureComputer(
    cache_size: int = 10000,
)
```

**Methods:**
- `compute_signature(message: str) -> str`: Compute signature with caching

---

## 🦀 Rust SDK API

### Core Types

#### `Config`

Configuration for LipService.

```rust
use lipservice::Config;

let config = Config {
    service_name: "my-service".to_string(),
    lipservice_url: "http://localhost:8000".to_string(),
    api_key: Some("api_key".to_string()),
    posthog_api_key: Some("phc_xxx".to_string()),
    posthog_team_id: Some("12345".to_string()),
    posthog_endpoint: "https://app.posthog.com".to_string(),
    batch_size: 100,
    flush_interval: Duration::from_secs(5),
    max_retries: 3,
    timeout: Duration::from_secs(10),
    policy_refresh_interval: Duration::from_secs(300),
    pattern_report_interval: Duration::from_secs(600),
};
```

#### `LipService`

Main LipService client.

```rust
use lipservice::LipService;

let mut ls = LipService::new(config).await?;
let logger = ls.logger();
ls.shutdown().await?;
```

**Methods:**
- `new(config: Config) -> Result<Self>`: Create new LipService instance
- `logger() -> Arc<LipServiceLogger>`: Get the logger
- `shutdown(self) -> Result<()>`: Shutdown the instance

#### `LipServiceLogger`

LipService logger with sampling and PostHog integration.

```rust
use lipservice::LipServiceLogger;

logger.info("User logged in");
logger.warn("High memory usage");
logger.error("Database connection failed");
logger.debug("Cache hit");
logger.fatal("System critical error");
```

**Methods:**
- `info(&self, message: &str)`: Log info message
- `warn(&self, message: &str)`: Log warning message
- `error(&self, message: &str)`: Log error message
- `debug(&self, message: &str)`: Log debug message
- `fatal(&self, message: &str)`: Log fatal message

---

## 🐹 Go SDK API

### Core Types

#### `Config`

Configuration for LipService.

```go
import "github.com/srex-dev/lipservice-go"

config := lipservice.Config{
    ServiceName:    "my-service",
    LipServiceURL:  "http://localhost:8000",
    APIKey:         "api_key",
    PostHogAPIKey:  "phc_xxx",
    PostHogTeamID:  "12345",
    PostHogEndpoint: "https://app.posthog.com",
    BatchSize:      100,
    FlushInterval:  5 * time.Second,
    MaxRetries:     3,
    Timeout:        10 * time.Second,
}
```

#### `LipService`

Main LipService client.

```go
ls, err := lipservice.New(config)
if err != nil {
    log.Fatal(err)
}
defer ls.Close()

logger := ls.Logger()
```

**Methods:**
- `New(config Config) (*LipService, error)`: Create new LipService instance
- `Logger() *LipServiceLogger`: Get the logger
- `Close() error`: Close the instance

#### `LipServiceLogger`

LipService logger with sampling and PostHog integration.

```go
logger.Info("User logged in", "user_id", 123)
logger.Warn("High memory usage", "usage", 85)
logger.Error("Database connection failed", "error", "timeout")
logger.Debug("Cache hit", "key", "user:123")
logger.Fatal("System critical error", "error", "panic")
```

**Methods:**
- `Info(msg string, args ...interface{})`: Log info message
- `Warn(msg string, args ...interface{})`: Log warning message
- `Error(msg string, args ...interface{})`: Log error message
- `Debug(msg string, args ...interface{})`: Log debug message
- `Fatal(msg string, args ...interface{})`: Log fatal message
- `With(args ...interface{}) *LipServiceLogger`: Add context
- `WithContext(ctx context.Context) *LipServiceLogger`: Add context

---

## 🔧 Backend API

### Endpoints

#### `GET /api/v1/policies/active`

Get the active sampling policy.

**Response:**
```json
{
  "policy_id": "policy_123",
  "sampling_rate": 0.1,
  "patterns": ["error", "warning"],
  "max_logs_per_minute": 1000,
  "severity_rates": {
    "ERROR": 1.0,
    "WARNING": 0.5,
    "INFO": 0.1,
    "DEBUG": 0.05
  }
}
```

#### `POST /api/v1/patterns/report`

Report pattern statistics.

**Request:**
```json
{
  "patterns": [
    {
      "signature": "abc123",
      "count": 100,
      "last_seen": "2023-01-01T12:00:00Z",
      "sampling_rate": 0.1
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "patterns_processed": 1
}
```

#### `POST /api/v1/policies/generate`

Generate a new sampling policy using AI.

**Request:**
```json
{
  "patterns": [
    {
      "signature": "abc123",
      "count": 100,
      "frequency": 0.1
    }
  ],
  "cost_target": 0.5,
  "llm_provider": "openai"
}
```

**Response:**
```json
{
  "policy_id": "policy_124",
  "sampling_rate": 0.05,
  "patterns": ["error", "warning", "info"],
  "max_logs_per_minute": 500,
  "severity_rates": {
    "ERROR": 1.0,
    "WARNING": 0.8,
    "INFO": 0.05,
    "DEBUG": 0.01
  },
  "cost_reduction": 0.75
}
```

---

## 📊 Performance Metrics

### Benchmarks

#### Python SDK
- **Signature Computation**: ~1,200 ns/op
- **Adaptive Sampling**: ~150 ns/op
- **PostHog Export**: ~2,000 ns/op
- **Memory Usage**: < 50MB for 1M logs/hour
- **Throughput**: > 10K logs/second

#### Go SDK
- **Signature Computation**: ~800 ns/op
- **Adaptive Sampling**: ~100 ns/op
- **PostHog Export**: ~1,500 ns/op
- **Memory Usage**: < 10MB for 1M logs/hour
- **Throughput**: > 50K logs/second

#### Rust SDK
- **Signature Computation**: ~600 ns/op
- **Adaptive Sampling**: ~80 ns/op
- **PostHog Export**: ~1,200 ns/op
- **Memory Usage**: < 5MB for 1M logs/hour
- **Throughput**: > 100K logs/second

### Performance Targets

- **Memory Usage**: < 50MB for 1M logs/hour
- **CPU Usage**: < 5% overhead on application
- **Latency**: < 1ms per log message
- **Throughput**: > 10K logs/second
- **Batch Efficiency**: > 95% successful exports

---

## 🔒 Security Considerations

### Input Validation

All inputs are validated and sanitized:
- Malicious input detection
- Large input handling
- Special character processing
- Injection attack prevention

### Authentication

- JWT-based authentication with PostHog
- API key validation
- Team ID isolation
- Secure credential handling

### Data Protection

- Sensitive data sanitization
- Pattern normalization
- Secure signature computation
- No sensitive data in signatures

---

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

COPY . /app
WORKDIR /app

RUN pip install -e .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  lipservice:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/lipservice
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=lipservice
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

  redis:
    image: redis:7
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for LLM integration
- `ANTHROPIC_API_KEY`: Anthropic API key for LLM integration
- `POSTHOG_API_KEY`: PostHog API key for integration
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## 📝 Examples

### Python Example

```python
from lipservice import configure_adaptive_logging, get_logger

# Configure LipService
configure_adaptive_logging(
    service_name="my-api",
    lipservice_url="https://lipservice.company.com",
    posthog_api_key="phc_xxx",
    posthog_team_id="12345",
)

# Use LipService logger
logger = get_logger(__name__)
logger.info("User logged in", user_id=123)
logger.error("Database connection failed", error="timeout")
```

### Go Example

```go
package main

import (
    "log"
    "time"
    
    "github.com/srex-dev/lipservice-go"
)

func main() {
    config := lipservice.Config{
        ServiceName:    "my-go-service",
        LipServiceURL:  "https://lipservice.company.com",
        PostHogAPIKey:  "phc_xxx",
        PostHogTeamID:  "12345",
    }

    ls, err := lipservice.New(config)
    if err != nil {
        log.Fatal(err)
    }
    defer ls.Close()

    logger := ls.Logger()
    logger.Info("User logged in", "user_id", 123)
    logger.Error("Database connection failed", "error", "timeout")
}
```

### Rust Example

```rust
use lipservice::{LipService, Config};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = Config {
        service_name: "my-rust-service".to_string(),
        lipservice_url: "https://lipservice.company.com".to_string(),
        posthog_api_key: Some("phc_xxx".to_string()),
        posthog_team_id: Some("12345".to_string()),
        ..Default::default()
    };

    let mut ls = LipService::new(config).await?;
    let logger = ls.logger();

    logger.info("User logged in", user_id = 123);
    logger.error("Database connection failed", error = "timeout");

    ls.shutdown().await?;
    Ok(())
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### "RuntimeError: no running event loop"
This error occurs when using async functions in a synchronous context. Use the synchronous methods or ensure an event loop is running.

#### "ModuleNotFoundError: No module named 'lipservice'"
Install LipService: `pip install lipservice[posthog]`

#### "PostHog export failed"
Check your PostHog API key and team ID. Ensure the PostHog endpoint is accessible.

#### "Signature computation too slow"
Use the optimized signature computer from the performance module.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues

1. Use the performance module for optimized operations
2. Increase batch size for better throughput
3. Use connection pooling for PostHog exports
4. Monitor memory usage with the performance profiler

---

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/srex-dev/lipservice/wiki)
- **Issues**: [GitHub Issues](https://github.com/srex-dev/lipservice/issues)
- **Discussions**: [GitHub Discussions](https://github.com/srex-dev/lipservice/discussions)
- **Email**: support@lipservice.dev

---

**Built with ❤️ and 🤖 for intelligent logging**
