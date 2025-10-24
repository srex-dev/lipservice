from datetime import datetime, timedelta
from typing import Optional

import httpx
import structlog
from clickhouse_driver import Client as ClickHouseClient

from src.engine.pattern_analyzer import LogEntry

logger = structlog.get_logger(__name__)


class PostHogLogsClient:
    """
    Client for fetching logs from PostHog.

    Supports two modes:
    1. Direct ClickHouse queries (fastest, requires ClickHouse access)
    2. PostHog REST API (easier, uses PostHog's query endpoint)
    """

    def __init__(
        self,
        clickhouse_host: str | None = None,
        clickhouse_port: int = 9000,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize PostHog logs client.

        Args:
            clickhouse_host: ClickHouse hostname (for direct queries)
            clickhouse_port: ClickHouse port
            api_url: PostHog API URL (e.g., https://app.posthog.com)
            api_key: PostHog API key
        """
        self.clickhouse_host = clickhouse_host
        self.clickhouse_port = clickhouse_port
        self.api_url = api_url
        self.api_key = api_key

        self.clickhouse_client: Optional[ClickHouseClient] = None
        if clickhouse_host:
            self.clickhouse_client = ClickHouseClient(
                host=clickhouse_host,
                port=clickhouse_port,
                database="default",
            )

    async def fetch_logs(
        self,
        team_id: int,
        service_name: str | None = None,
        hours: int = 1,
        limit: int = 10000,
    ) -> list[LogEntry]:
        """
        Fetch logs from PostHog.

        Args:
            team_id: PostHog team ID
            service_name: Filter by service name (optional)
            hours: Hours of logs to fetch
            limit: Maximum number of logs

        Returns:
            List of LogEntry objects
        """
        if self.clickhouse_client:
            return await self._fetch_from_clickhouse(team_id, service_name, hours, limit)
        elif self.api_url and self.api_key:
            return await self._fetch_from_api(team_id, service_name, hours, limit)
        else:
            raise ValueError("Either ClickHouse client or API credentials required")

    async def _fetch_from_clickhouse(
        self, team_id: int, service_name: str | None, hours: int, limit: int
    ) -> list[LogEntry]:
        """
        Fetch logs directly from ClickHouse (fastest method).

        Queries PostHog's 'logs' table directly.
        """
        where_clauses = [f"team_id = {team_id}", f"timestamp >= now() - INTERVAL {hours} HOUR"]

        if service_name:
            where_clauses.append(f"service_name = '{service_name}'")

        query = f"""
        SELECT 
            body,
            severity_text,
            timestamp,
            service_name
        FROM logs
        WHERE {' AND '.join(where_clauses)}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """

        logger.info("Fetching logs from ClickHouse", team_id=team_id, service_name=service_name, hours=hours)

        try:
            rows = self.clickhouse_client.execute(query)

            logs = [
                LogEntry(
                    message=row[0] or "",
                    severity=row[1] or "INFO",
                    timestamp=row[2] if isinstance(row[2], datetime) else datetime.fromisoformat(str(row[2])),
                    service_name=row[3] or "unknown",
                )
                for row in rows
            ]

            logger.info("Fetched logs from ClickHouse", count=len(logs))
            return logs

        except Exception as e:
            logger.error("Failed to fetch logs from ClickHouse", error=str(e))
            raise

    async def _fetch_from_api(
        self, team_id: int, service_name: str | None, hours: int, limit: int
    ) -> list[LogEntry]:
        """
        Fetch logs via PostHog REST API.

        Uses PostHog's /api/projects/@current/logs/query endpoint.
        """
        date_from = datetime.now() - timedelta(hours=hours)

        query_data = {
            "query": {
                "dateRange": {"from": date_from.isoformat()},
                "limit": limit,
            }
        }

        if service_name:
            query_data["query"]["serviceNames"] = [service_name]

        logger.info("Fetching logs from PostHog API", team_id=team_id, service_name=service_name)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/projects/{team_id}/logs/query",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=query_data,
                    timeout=30.0,
                )

                response.raise_for_status()
                data = response.json()

                logs = [
                    LogEntry(
                        message=result.get("body", ""),
                        severity=result.get("severity_text", "INFO"),
                        timestamp=datetime.fromisoformat(result.get("timestamp")),
                        service_name=result.get("service_name", "unknown"),
                    )
                    for result in data.get("results", [])
                ]

                logger.info("Fetched logs from PostHog API", count=len(logs))
                return logs

            except httpx.HTTPError as e:
                logger.error("Failed to fetch logs from PostHog API", error=str(e))
                raise

    def get_log_volume(self, team_id: int, service_name: str, hours: int = 24) -> int:
        """
        Get total log volume for cost estimation.

        Args:
            team_id: PostHog team ID
            service_name: Service name
            hours: Time window

        Returns:
            Total number of logs
        """
        if not self.clickhouse_client:
            raise ValueError("ClickHouse client required for volume queries")

        query = f"""
        SELECT COUNT(*)
        FROM logs
        WHERE team_id = {team_id}
          AND service_name = '{service_name}'
          AND timestamp >= now() - INTERVAL {hours} HOUR
        """

        try:
            result = self.clickhouse_client.execute(query)
            return result[0][0] if result else 0
        except Exception as e:
            logger.error("Failed to get log volume", error=str(e))
            return 0

    def get_active_services(self, team_id: int, hours: int = 24) -> list[str]:
        """
        Get list of active services for a team.

        Args:
            team_id: PostHog team ID
            hours: Time window to check for activity

        Returns:
            List of service names
        """
        if not self.clickhouse_client:
            raise ValueError("ClickHouse client required for service queries")

        query = f"""
        SELECT DISTINCT service_name
        FROM logs
        WHERE team_id = {team_id}
          AND timestamp >= now() - INTERVAL {hours} HOUR
        ORDER BY service_name
        """

        try:
            rows = self.clickhouse_client.execute(query)
            return [row[0] for row in rows if row[0]]
        except Exception as e:
            logger.error("Failed to get active services", error=str(e))
            return []

