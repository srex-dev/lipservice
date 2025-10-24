"""Adaptive sampling engine for intelligent log filtering."""

import asyncio
import random
from collections import defaultdict
from datetime import datetime
from typing import Any

import structlog

from lipservice.client import LipServiceClient
from lipservice.models import PatternStats, SamplingPolicy
from lipservice.signature import compute_signature

logger = structlog.get_logger(__name__)


class AdaptiveSampler:
    """
    Intelligent log sampler that makes sampling decisions based on AI policies.

    Features:
    - Pattern-based sampling rates
    - Severity-based sampling rates
    - Always keeps ERROR and CRITICAL logs
    - Anomaly detection boost
    - Pattern statistics tracking
    """

    # Always sample these severity levels
    ALWAYS_SAMPLE_SEVERITIES = {"ERROR", "CRITICAL", "FATAL"}

    def __init__(
        self,
        client: LipServiceClient,
        policy_refresh_interval: int = 300,
        pattern_report_interval: int = 600,
        max_pattern_cache_size: int = 10000,
    ):
        """
        Initialize adaptive sampler.

        Args:
            client: LipService API client
            policy_refresh_interval: Seconds between policy refreshes
            pattern_report_interval: Seconds between pattern reports
            max_pattern_cache_size: Maximum patterns to track
        """
        self.client = client
        self.policy_refresh_interval = policy_refresh_interval
        self.pattern_report_interval = pattern_report_interval
        self.max_pattern_cache_size = max_pattern_cache_size

        self.policy: SamplingPolicy | None = None
        self.pattern_stats: dict[str, dict[str, Any]] = defaultdict(self._default_pattern_stats)

        self._policy_task: asyncio.Task | None = None
        self._report_task: asyncio.Task | None = None
        self._running = False

    def _default_pattern_stats(self) -> dict[str, Any]:
        """Default pattern statistics structure."""
        now = datetime.now()
        return {
            "count": 0,
            "message_sample": "",
            "severity_distribution": defaultdict(int),
            "first_seen": now,
            "last_seen": now,
        }

    async def start(self) -> None:
        """Start background tasks for policy refresh and pattern reporting."""
        if self._running:
            return

        self._running = True

        # Fetch initial policy
        await self._refresh_policy()

        # Start background tasks
        self._policy_task = asyncio.create_task(self._policy_refresh_loop())
        self._report_task = asyncio.create_task(self._pattern_report_loop())

        logger.info("sampler_started", service=self.client.service_name)

    async def stop(self) -> None:
        """Stop background tasks and report final statistics."""
        if not self._running:
            return

        self._running = False

        # Cancel background tasks
        if self._policy_task:
            self._policy_task.cancel()
            try:
                await self._policy_task
            except asyncio.CancelledError:
                pass

        if self._report_task:
            self._report_task.cancel()
            try:
                await self._report_task
            except asyncio.CancelledError:
                pass

        # Report final patterns
        await self._report_patterns()

        logger.info("sampler_stopped", service=self.client.service_name)

    def should_sample(self, message: str, severity: str, **context: Any) -> tuple[bool, str]:
        """
        Decide whether to sample this log entry.

        Args:
            message: Log message
            severity: Log severity level
            **context: Additional context

        Returns:
            Tuple of (should_sample: bool, signature: str)
        """
        severity_upper = severity.upper()

        # Always sample errors and critical logs
        if severity_upper in self.ALWAYS_SAMPLE_SEVERITIES:
            signature = compute_signature(message)
            self._track_pattern(signature, message, severity_upper)
            return True, signature

        # Compute pattern signature
        signature = compute_signature(message)

        # Track pattern statistics
        self._track_pattern(signature, message, severity_upper)

        # If no policy, use fallback rate (default: 1.0 = 100%)
        if not self.policy:
            return True, signature

        # Check for pattern-specific rate
        pattern_rate = self.policy.get_pattern_rate(signature)
        if pattern_rate is not None:
            decision = random.random() < pattern_rate
            return decision, signature

        # Use severity-based rate
        severity_rate = self.policy.get_severity_rate(severity_upper)
        decision = random.random() < severity_rate

        return decision, signature

    def _track_pattern(self, signature: str, message: str, severity: str) -> None:
        """Track pattern statistics for reporting."""
        # Don't track if cache is too large
        if signature not in self.pattern_stats and len(self.pattern_stats) >= self.max_pattern_cache_size:
            return

        stats = self.pattern_stats[signature]
        stats["count"] += 1
        stats["last_seen"] = datetime.now()

        if not stats["message_sample"]:
            stats["message_sample"] = message[:200]  # Truncate long messages

        stats["severity_distribution"][severity] += 1

    async def _refresh_policy(self) -> None:
        """Fetch latest policy from LipService."""
        try:
            policy = await self.client.get_active_policy()
            if policy:
                old_version = self.policy.version if self.policy else 0
                self.policy = policy
                logger.info(
                    "policy_updated",
                    service=self.client.service_name,
                    version=policy.version,
                    old_version=old_version,
                    global_rate=policy.global_rate,
                )
        except Exception as e:
            logger.error("policy_refresh_failed", service=self.client.service_name, error=str(e))

    async def _report_patterns(self) -> None:
        """Report pattern statistics to LipService."""
        if not self.pattern_stats:
            return

        try:
            patterns = [
                PatternStats(
                    signature=sig,
                    message_sample=stats["message_sample"],
                    count=stats["count"],
                    severity_distribution=dict(stats["severity_distribution"]),
                    first_seen=stats["first_seen"],
                    last_seen=stats["last_seen"],
                )
                for sig, stats in self.pattern_stats.items()
            ]

            success = await self.client.report_patterns(patterns)

            if success:
                # Clear reported patterns
                self.pattern_stats.clear()
                logger.info("patterns_reported", service=self.client.service_name, count=len(patterns))

        except Exception as e:
            logger.error("pattern_report_failed", service=self.client.service_name, error=str(e))

    async def _policy_refresh_loop(self) -> None:
        """Background loop for periodic policy refresh."""
        while self._running:
            try:
                await asyncio.sleep(self.policy_refresh_interval)
                await self._refresh_policy()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("policy_refresh_loop_error", error=str(e))

    async def _pattern_report_loop(self) -> None:
        """Background loop for periodic pattern reporting."""
        while self._running:
            try:
                await asyncio.sleep(self.pattern_report_interval)
                await self._report_patterns()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("pattern_report_loop_error", error=str(e))

    def get_stats(self) -> dict[str, Any]:
        """Get current sampler statistics."""
        return {
            "policy_version": self.policy.version if self.policy else None,
            "patterns_tracked": len(self.pattern_stats),
            "total_logs_seen": sum(stats["count"] for stats in self.pattern_stats.values()),
        }

