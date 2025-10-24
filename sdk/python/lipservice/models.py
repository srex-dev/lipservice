"""Data models for LipService SDK."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SamplingPolicy(BaseModel):
    """Sampling policy received from LipService API."""

    version: int = Field(description="Policy version number")
    global_rate: float = Field(ge=0.0, le=1.0, description="Global sampling rate")
    severity_rates: dict[str, float] = Field(default_factory=dict, description="Per-severity sampling rates")
    pattern_rates: dict[str, float] = Field(default_factory=dict, description="Per-pattern sampling rates")
    anomaly_boost: float = Field(ge=1.0, description="Anomaly detection sampling multiplier")
    reasoning: str | None = Field(None, description="AI reasoning for policy decisions")
    created_at: datetime | None = Field(None, description="Policy creation timestamp")

    def get_severity_rate(self, severity: str) -> float:
        """Get sampling rate for a severity level."""
        return self.severity_rates.get(severity.upper(), self.global_rate)

    def get_pattern_rate(self, signature: str) -> float | None:
        """Get sampling rate for a specific pattern signature."""
        return self.pattern_rates.get(signature)


class PatternStats(BaseModel):
    """Statistics about a log pattern for reporting back to LipService."""

    signature: str = Field(description="Pattern signature")
    message_sample: str = Field(description="Representative message sample")
    count: int = Field(ge=0, description="Number of occurrences")
    severity_distribution: dict[str, int] = Field(default_factory=dict, description="Severity counts")
    first_seen: datetime = Field(description="First occurrence timestamp")
    last_seen: datetime = Field(description="Last occurrence timestamp")


class LogContext(BaseModel):
    """Additional context for log entries."""

    user_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        result = {}
        if self.user_id:
            result["user_id"] = self.user_id
        if self.request_id:
            result["request_id"] = self.request_id
        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.span_id:
            result["span_id"] = self.span_id
        result.update(self.custom_fields)
        return result


class SDKConfig(BaseModel):
    """Configuration for LipService SDK."""

    service_name: str = Field(description="Service identifier")
    lipservice_url: str = Field(description="LipService API URL")
    api_key: str | None = Field(None, description="API key for authentication")
    policy_refresh_interval: int = Field(default=300, description="Policy refresh interval in seconds")
    pattern_report_interval: int = Field(default=600, description="Pattern reporting interval in seconds")
    enable_pattern_detection: bool = Field(default=True, description="Enable client-side pattern detection")
    enable_policy_sampling: bool = Field(default=True, description="Enable policy-based sampling")
    fallback_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Fallback rate when policy unavailable")
    max_pattern_cache_size: int = Field(default=10000, description="Maximum patterns to cache")

