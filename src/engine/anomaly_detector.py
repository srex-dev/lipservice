from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np


@dataclass
class Anomaly:
    """Represents a detected anomaly."""

    pattern_signature: str
    anomaly_type: str  # 'rate_spike', 'new_pattern', 'error_surge'
    severity: str  # 'low', 'medium', 'high'
    current_value: float
    baseline_value: float
    confidence: float  # 0.0 to 1.0
    detected_at: datetime
    message: str


class AnomalyDetector:
    """
    Detects anomalies in log patterns using statistical methods.

    Uses sliding windows and Z-score analysis to detect:
    - Rate spikes (sudden increase in log volume)
    - New patterns (never seen before)
    - Error surges (increase in error severity logs)
    """

    def __init__(self, window_size: int = 1000, z_threshold: float = 3.0):
        """
        Initialize anomaly detector.

        Args:
            window_size: Size of sliding window for rate calculation
            z_threshold: Z-score threshold for anomaly detection (typically 3.0)
        """
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.rate_window: deque[float] = deque(maxlen=window_size)

    def detect_rate_anomaly(self, current_rate: float, baseline_rate: float) -> Anomaly | None:
        """
        Detect if current rate is anomalously high compared to baseline.

        Uses simple ratio comparison: current > threshold * baseline

        Args:
            current_rate: Current logs per second
            baseline_rate: Historical logs per second

        Returns:
            Anomaly if detected, else None
        """
        if baseline_rate == 0:
            return None

        ratio = current_rate / baseline_rate

        if ratio >= 5.0:
            severity = "high"
            confidence = min(ratio / 10.0, 1.0)
        elif ratio >= 3.0:
            severity = "medium"
            confidence = 0.7
        elif ratio >= 2.0:
            severity = "low"
            confidence = 0.5
        else:
            return None

        return Anomaly(
            pattern_signature="global_rate",
            anomaly_type="rate_spike",
            severity=severity,
            current_value=current_rate,
            baseline_value=baseline_rate,
            confidence=confidence,
            detected_at=datetime.now(),
            message=f"Log rate spike detected: {ratio:.1f}x normal rate",
        )

    def detect_with_zscore(self, values: list[float], current_value: float) -> Anomaly | None:
        """
        Detect anomaly using Z-score method.

        Z-score = (value - mean) / std_dev
        Anomaly if |z-score| > threshold

        Args:
            values: Historical values
            current_value: Current value to check

        Returns:
            Anomaly if detected, else None
        """
        if len(values) < 2:
            return None

        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return None

        z_score = abs((current_value - mean) / std)

        if z_score <= self.z_threshold:
            return None

        severity = "high" if z_score > 5 else "medium" if z_score > 4 else "low"

        return Anomaly(
            pattern_signature="zscore_analysis",
            anomaly_type="rate_spike",
            severity=severity,
            current_value=current_value,
            baseline_value=mean,
            confidence=min(z_score / 10.0, 1.0),
            detected_at=datetime.now(),
            message=f"Z-score anomaly: {z_score:.2f} (threshold: {self.z_threshold})",
        )

    def detect_error_surge(
        self, current_error_rate: float, baseline_error_rate: float, total_logs: int
    ) -> Anomaly | None:
        """
        Detect surge in error-level logs.

        More sensitive than general rate detection because errors
        are critical for observability.

        Args:
            current_error_rate: Current error rate (errors per second)
            baseline_error_rate: Historical error rate
            total_logs: Total log count for context

        Returns:
            Anomaly if detected, else None
        """
        if baseline_error_rate == 0 and current_error_rate > 0:
            return Anomaly(
                pattern_signature="error_rate",
                anomaly_type="error_surge",
                severity="high",
                current_value=current_error_rate,
                baseline_value=0.0,
                confidence=0.9,
                detected_at=datetime.now(),
                message="New errors detected (previously zero error rate)",
            )

        if baseline_error_rate == 0:
            return None

        ratio = current_error_rate / baseline_error_rate

        if ratio >= 2.0:
            severity = "high" if ratio >= 4.0 else "medium"
            return Anomaly(
                pattern_signature="error_rate",
                anomaly_type="error_surge",
                severity=severity,
                current_value=current_error_rate,
                baseline_value=baseline_error_rate,
                confidence=min(ratio / 5.0, 1.0),
                detected_at=datetime.now(),
                message=f"Error surge detected: {ratio:.1f}x normal error rate",
            )

        return None

    def is_new_pattern(self, pattern_signature: str, known_signatures: set[str]) -> bool:
        """
        Check if pattern is new (never seen before).

        New patterns are important - always sample first occurrence.

        Args:
            pattern_signature: Signature to check
            known_signatures: Set of previously seen signatures

        Returns:
            True if pattern is new, False if seen before
        """
        return pattern_signature not in known_signatures

    def update_rate_window(self, timestamp: float) -> None:
        """
        Update sliding window with new log timestamp.

        Used for real-time rate calculation.

        Args:
            timestamp: Unix timestamp of new log
        """
        self.rate_window.append(timestamp)

    def get_current_rate(self, window_seconds: int = 10) -> float:
        """
        Calculate current logs per second in recent window.

        Args:
            window_seconds: Time window to calculate rate

        Returns:
            Logs per second in recent window
        """
        if len(self.rate_window) < 2:
            return 0.0

        now = datetime.now().timestamp()
        recent_logs = [t for t in self.rate_window if now - t < window_seconds]

        if len(recent_logs) < 2:
            return 0.0

        return len(recent_logs) / window_seconds

