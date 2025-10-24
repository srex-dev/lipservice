"""LipService API client for fetching policies and reporting patterns."""

from datetime import datetime
from typing import Any

import httpx
import structlog

from lipservice.models import PatternStats, SamplingPolicy

logger = structlog.get_logger(__name__)


class LipServiceClient:
    """
    Client for communicating with LipService API.

    Handles policy fetching and pattern statistics reporting.
    """

    def __init__(
        self,
        base_url: str,
        service_name: str,
        api_key: str | None = None,
        timeout: float = 10.0,
    ):
        """
        Initialize LipService client.

        Args:
            base_url: LipService API base URL
            service_name: Service identifier
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.api_key = api_key
        self.timeout = timeout

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    async def get_active_policy(self) -> SamplingPolicy | None:
        """
        Fetch active sampling policy for this service.

        Returns:
            SamplingPolicy if available, None otherwise
        """
        try:
            response = await self.client.get(f"/api/v1/policies/{self.service_name}")
            response.raise_for_status()

            data = response.json()

            return SamplingPolicy(
                version=data["version"],
                global_rate=data["global_rate"],
                severity_rates=data["severity_rates"],
                pattern_rates=data.get("pattern_rates", {}),
                anomaly_boost=data.get("anomaly_boost", 2.0),
                reasoning=data.get("reasoning"),
                created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info("no_policy_found", service=self.service_name)
                return None
            logger.error("policy_fetch_failed", service=self.service_name, status=e.response.status_code, error=str(e))
            return None

        except Exception as e:
            logger.error("policy_fetch_error", service=self.service_name, error=str(e))
            return None

    async def report_patterns(self, patterns: list[PatternStats]) -> bool:
        """
        Report pattern statistics to LipService.

        Args:
            patterns: List of pattern statistics

        Returns:
            True if successful, False otherwise
        """
        if not patterns:
            return True

        try:
            payload = {
                "service_name": self.service_name,
                "patterns": [
                    {
                        "signature": p.signature,
                        "message_sample": p.message_sample,
                        "count": p.count,
                        "severity_distribution": p.severity_distribution,
                        "first_seen": p.first_seen.isoformat(),
                        "last_seen": p.last_seen.isoformat(),
                    }
                    for p in patterns
                ],
            }

            response = await self.client.post("/api/v1/patterns/stats", json=payload)
            response.raise_for_status()

            logger.info("patterns_reported", service=self.service_name, count=len(patterns))
            return True

        except Exception as e:
            logger.error("pattern_report_failed", service=self.service_name, error=str(e))
            return False

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self) -> "LipServiceClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

