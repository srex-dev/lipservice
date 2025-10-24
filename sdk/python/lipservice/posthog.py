"""
PostHog OTLP exporter for LipService SDK.

Provides direct integration with PostHog's logging infrastructure
using the OpenTelemetry Protocol (OTLP).
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
import structlog
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, InstrumentationScope, KeyValue
from opentelemetry.proto.logs.v1.logs_pb2 import LogRecord, ResourceLogs, ScopeLogs
from opentelemetry.proto.resource.v1.resource_pb2 import Resource

from lipservice.models import LogContext

logger = structlog.get_logger(__name__)


class PostHogConfig:
    """Configuration for PostHog integration."""

    def __init__(
        self,
        api_key: str,
        team_id: str,
        endpoint: str = "https://app.posthog.com",
        timeout: float = 10.0,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize PostHog configuration.

        Args:
            api_key: PostHog API key (phc_xxx)
            team_id: PostHog team ID
            endpoint: PostHog endpoint (default: PostHog Cloud)
            timeout: Request timeout in seconds
            batch_size: Number of logs to batch before sending
            flush_interval: Seconds between batch flushes
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_key = api_key
        self.team_id = team_id
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries

        # OTLP endpoint
        self.otlp_endpoint = f"{self.endpoint}/api/v1/otlp/v1/logs"

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for PostHog requests."""
        return {
            "Content-Type": "application/x-protobuf",
            "Authorization": f"Bearer {self.api_key}",
            "X-PostHog-Team-Id": self.team_id,
        }


class PostHogOTLPExporter:
    """
    PostHog OTLP exporter for logs.

    Handles batching, retries, and OTLP protocol compliance.
    """

    def __init__(self, config: PostHogConfig):
        """
        Initialize PostHog OTLP exporter.

        Args:
            config: PostHog configuration
        """
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.endpoint,
            headers=config.get_headers(),
            timeout=config.timeout,
        )
        self.batch: list[LogRecord] = []
        self._running = False
        self._flush_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the exporter background tasks."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("posthog_exporter_started", endpoint=self.config.otlp_endpoint)

    async def stop(self) -> None:
        """Stop the exporter and flush remaining logs."""
        if not self._running:
            return

        self._running = False

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining logs
        if self.batch:
            await self._flush_batch()

        await self.client.aclose()
        logger.info("posthog_exporter_stopped")

    async def export_log(
        self,
        message: str,
        severity: str,
        timestamp: datetime,
        context: LogContext | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Export a single log to PostHog.

        Args:
            message: Log message
            severity: Log severity level
            timestamp: Log timestamp
            context: Additional log context
            **kwargs: Additional log attributes
        """
        # Create OTLP log record
        log_record = self._create_log_record(message, severity, timestamp, context, **kwargs)

        # Add to batch
        self.batch.append(log_record)

        # Flush if batch is full
        if len(self.batch) >= self.config.batch_size:
            await self._flush_batch()

    def _create_log_record(
        self,
        message: str,
        severity: str,
        timestamp: datetime,
        context: LogContext | None = None,
        **kwargs: Any,
    ) -> LogRecord:
        """Create an OTLP LogRecord."""
        # Convert timestamp to nanoseconds
        timestamp_ns = int(timestamp.timestamp() * 1_000_000_000)

        # Create attributes
        attributes = []

        # Add severity
        attributes.append(
            KeyValue(
                key="severity_text",
                value=AnyValue(string_value=severity),
            )
        )

        # Add severity number
        severity_number = self._get_severity_number(severity)
        attributes.append(
            KeyValue(
                key="severity_number",
                value=AnyValue(int_value=severity_number),
            )
        )

        # Add context attributes
        if context:
            context_dict = context.to_dict()
            for key, value in context_dict.items():
                attributes.append(
                    KeyValue(
                        key=f"context.{key}",
                        value=AnyValue(string_value=str(value)),
                    )
                )

        # Add additional attributes
        for key, value in kwargs.items():
            attributes.append(
                KeyValue(
                    key=str(key),
                    value=AnyValue(string_value=str(value)),
                )
            )

        return LogRecord(
            time_unix_nano=timestamp_ns,
            severity_text=severity,
            severity_number=severity_number,
            body=AnyValue(string_value=message),
            attributes=attributes,
        )

    def _get_severity_number(self, severity: str) -> int:
        """Convert severity string to OTLP severity number."""
        severity_map = {
            "TRACE": 1,
            "DEBUG": 5,
            "INFO": 9,
            "WARN": 13,
            "WARNING": 13,
            "ERROR": 17,
            "FATAL": 21,
            "CRITICAL": 21,
        }
        return severity_map.get(severity.upper(), 9)  # Default to INFO

    async def _flush_loop(self) -> None:
        """Background task to flush batches periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.config.flush_interval)
                if self.batch:
                    await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("flush_loop_error", error=str(e))

    async def _flush_batch(self) -> None:
        """Flush the current batch to PostHog."""
        if not self.batch:
            return

        # Create OTLP request
        request = self._create_otlp_request()

        # Send with retries
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.post(
                    self.config.otlp_endpoint,
                    content=request.SerializeToString(),
                )
                response.raise_for_status()

                logger.info(
                    "logs_exported",
                    count=len(self.batch),
                    attempt=attempt + 1,
                )
                break

            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 502, 503, 504]:
                    # Retryable error
                    if attempt < self.config.max_retries:
                        wait_time = 2**attempt  # Exponential backoff
                        logger.warning(
                            "export_retry",
                            status=e.response.status_code,
                            attempt=attempt + 1,
                            wait_time=wait_time,
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(
                            "export_failed_max_retries",
                            status=e.response.status_code,
                            count=len(self.batch),
                        )
                        break
                else:
                    # Non-retryable error
                    logger.error(
                        "export_failed_non_retryable",
                        status=e.response.status_code,
                        count=len(self.batch),
                    )
                    break

            except Exception as e:
                logger.error("export_error", error=str(e), attempt=attempt + 1)
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2**attempt)
                else:
                    break

        # Clear batch
        self.batch.clear()

    def _create_otlp_request(self) -> ExportLogsServiceRequest:
        """Create OTLP ExportLogsServiceRequest."""
        # Create resource
        resource = Resource(
            attributes=[
                KeyValue(
                    key="service.name",
                    value=AnyValue(string_value="lipservice-sdk"),
                ),
                KeyValue(
                    key="service.version",
                    value=AnyValue(string_value="0.2.0"),
                ),
            ]
        )

        # Create scope
        scope_logs = ScopeLogs(
            scope=InstrumentationScope(
                name="lipservice",
                version="0.2.0",
            ),
            log_records=self.batch,
        )

        # Create resource logs
        resource_logs = ResourceLogs(
            resource=resource,
            scope_logs=[scope_logs],
        )

        return ExportLogsServiceRequest(resource_logs=[resource_logs])


class PostHogHandler(logging.Handler):
    """
    Logging handler that sends logs to PostHog via OTLP.

    Integrates with LipService's intelligent sampling.
    """

    def __init__(
        self,
        config: PostHogConfig,
        level: int = logging.NOTSET,
    ):
        """
        Initialize PostHog handler.

        Args:
            config: PostHog configuration
            level: Logging level
        """
        super().__init__(level)
        self.config = config
        self.exporter = PostHogOTLPExporter(config)
        self._started = False

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit log record to PostHog.

        Args:
            record: LogRecord to emit
        """
        try:
            # Start exporter if not started
            if not self._started:
                asyncio.create_task(self.exporter.start())
                self._started = True

            # Extract message
            message = self.format(record) if not record.getMessage() else record.getMessage()

            # Extract severity
            severity = record.levelname

            # Extract timestamp
            timestamp = datetime.fromtimestamp(record.created)

            # Extract context from record
            context = None
            if hasattr(record, "lipservice_context"):
                context = record.lipservice_context

            # Extract additional attributes
            attributes = {}
            if hasattr(record, "lipservice_signature"):
                attributes["lipservice_signature"] = record.lipservice_signature
            if hasattr(record, "lipservice_sampled"):
                attributes["lipservice_sampled"] = record.lipservice_sampled

            # Add standard logging attributes
            attributes.update({
                "logger_name": record.name,
                "module": record.module,
                "function": record.funcName,
                "line_number": record.lineno,
            })

            # Export to PostHog
            asyncio.create_task(
                self.exporter.export_log(
                    message=message,
                    severity=severity,
                    timestamp=timestamp,
                    context=context,
                    **attributes,
                )
            )

        except Exception as e:
            self.handleError(record)
            logger.error("posthog_handler_error", error=str(e))

    def close(self) -> None:
        """Close handler and flush remaining logs."""
        try:
            if self._started:
                asyncio.run(self.exporter.stop())
        except Exception as e:
            logger.error("posthog_handler_close_error", error=str(e))

        super().close()


def create_posthog_handler(
    api_key: str,
    team_id: str,
    endpoint: str = "https://app.posthog.com",
    **kwargs: Any,
) -> PostHogHandler:
    """
    Create a PostHog logging handler.

    Args:
        api_key: PostHog API key (phc_xxx)
        team_id: PostHog team ID
        endpoint: PostHog endpoint (default: PostHog Cloud)
        **kwargs: Additional configuration options

    Returns:
        PostHogHandler instance

    Example:
        >>> handler = create_posthog_handler(
        ...     api_key="phc_xxx",
        ...     team_id="12345"
        ... )
        >>> logging.root.addHandler(handler)
    """
    config = PostHogConfig(api_key=api_key, team_id=team_id, endpoint=endpoint, **kwargs)
    return PostHogHandler(config)
