"""
Optimized PostHog OTLP exporter with connection pooling and async processing.

This module provides:
- HTTP connection pooling
- Async batch processing
- Memory-efficient OTLP serialization
- Performance monitoring
"""

import asyncio
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

import httpx
import structlog
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, InstrumentationScope, KeyValue
from opentelemetry.proto.logs.v1.logs_pb2 import LogRecord, ResourceLogs, ScopeLogs
from opentelemetry.proto.resource.v1.resource_pb2 import Resource

from lipservice.models import LogContext
from lipservice.performance import get_memory_pool, get_signature_cache

logger = structlog.get_logger(__name__)


class ConnectionPool:
    """
    HTTP connection pool for efficient PostHog communication.
    """
    
    def __init__(self, base_url: str, headers: Dict[str, str], timeout: float = 10.0):
        """
        Initialize connection pool.
        
        Args:
            base_url: Base URL for PostHog
            headers: HTTP headers
            timeout: Request timeout
        """
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = httpx.AsyncClient(
                        base_url=self.base_url,
                        headers=self.headers,
                        timeout=self.timeout,
                        limits=httpx.Limits(
                            max_keepalive_connections=20,
                            max_connections=100,
                            keepalive_expiry=30.0,
                        ),
                    )
        return self._client
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None


class OptimizedPostHogOTLPExporter:
    """
    Optimized PostHog OTLP exporter with performance improvements.
    
    Features:
    - Connection pooling
    - Async batch processing
    - Memory-efficient serialization
    - Performance monitoring
    """
    
    def __init__(
        self,
        api_key: str,
        team_id: str,
        endpoint: str = "https://app.posthog.com",
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        timeout: float = 10.0,
    ):
        """
        Initialize optimized PostHog OTLP exporter.
        
        Args:
            api_key: PostHog API key
            team_id: PostHog team ID
            endpoint: PostHog endpoint
            batch_size: Batch size for exports
            flush_interval: Flush interval in seconds
            max_retries: Maximum retry attempts
            timeout: Request timeout
        """
        self.api_key = api_key
        self.team_id = team_id
        self.endpoint = endpoint.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.timeout = timeout
        
        # OTLP endpoint
        self.otlp_endpoint = f"{self.endpoint}/api/v1/otlp/v1/logs"
        
        # Connection pool
        headers = {
            "Content-Type": "application/x-protobuf",
            "Authorization": f"Bearer {self.api_key}",
            "X-PostHog-Team-Id": self.team_id,
        }
        self.connection_pool = ConnectionPool(self.endpoint, headers, timeout)
        
        # Batch processing
        self.batch: deque = deque()
        self._lock = threading.Lock()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        
        # Performance monitoring
        self._stats = {
            'logs_exported': 0,
            'batches_sent': 0,
            'errors': 0,
            'retries': 0,
            'last_flush_time': 0,
            'avg_batch_size': 0,
        }
        
        # Memory pool for efficient operations
        self.memory_pool = get_memory_pool()
    
    async def start(self) -> None:
        """Start the exporter background tasks."""
        if self._running:
            return
        
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("optimized_posthog_exporter_started", endpoint=self.otlp_endpoint)
    
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
        
        # Close connection pool
        await self.connection_pool.close()
        logger.info("optimized_posthog_exporter_stopped")
    
    async def export_log(
        self,
        message: str,
        severity: str,
        timestamp: float,
        context: Optional[LogContext] = None,
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
        # Create log record
        log_record = self._create_log_record(message, severity, timestamp, context, **kwargs)
        
        # Add to batch
        with self._lock:
            self.batch.append(log_record)
            
            # Flush if batch is full
            if len(self.batch) >= self.batch_size:
                # Create a copy of the batch and clear it
                batch_to_send = list(self.batch)
                self.batch.clear()
                
                # Submit flush task
                asyncio.create_task(self._flush_batch_async(batch_to_send))
    
    def _create_log_record(
        self,
        message: str,
        severity: str,
        timestamp: float,
        context: Optional[LogContext] = None,
        **kwargs: Any,
    ) -> LogRecord:
        """Create an OTLP LogRecord efficiently."""
        # Convert timestamp to nanoseconds
        timestamp_ns = int(timestamp * 1_000_000_000)
        
        # Create attributes efficiently
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
                await asyncio.sleep(self.flush_interval)
                
                with self._lock:
                    if self.batch:
                        batch_to_send = list(self.batch)
                        self.batch.clear()
                    else:
                        batch_to_send = []
                
                if batch_to_send:
                    await self._flush_batch_async(batch_to_send)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("flush_loop_error", error=str(e))
                self._stats['errors'] += 1
    
    async def _flush_batch(self) -> None:
        """Flush the current batch to PostHog."""
        with self._lock:
            if not self.batch:
                return
            
            batch_to_send = list(self.batch)
            self.batch.clear()
        
        await self._flush_batch_async(batch_to_send)
    
    async def _flush_batch_async(self, batch: List[LogRecord]) -> None:
        """Flush a batch to PostHog asynchronously."""
        if not batch:
            return
        
        # Create OTLP request
        request = self._create_otlp_request(batch)
        
        # Get HTTP client
        client = await self.connection_pool.get_client()
        
        # Send with retries
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.post(
                    self.otlp_endpoint,
                    content=request.SerializeToString(),
                )
                response.raise_for_status()
                
                # Update stats
                self._stats['logs_exported'] += len(batch)
                self._stats['batches_sent'] += 1
                self._stats['last_flush_time'] = time.time()
                self._stats['avg_batch_size'] = (
                    (self._stats['avg_batch_size'] * (self._stats['batches_sent'] - 1) + len(batch)) /
                    self._stats['batches_sent']
                )
                
                logger.info(
                    "logs_exported_optimized",
                    count=len(batch),
                    attempt=attempt + 1,
                )
                break
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 502, 503, 504]:
                    # Retryable error
                    if attempt < self.max_retries:
                        wait_time = 2**attempt  # Exponential backoff
                        logger.warning(
                            "export_retry_optimized",
                            status=e.response.status_code,
                            attempt=attempt + 1,
                            wait_time=wait_time,
                        )
                        await asyncio.sleep(wait_time)
                        self._stats['retries'] += 1
                        continue
                    else:
                        logger.error(
                            "export_failed_max_retries_optimized",
                            status=e.response.status_code,
                            count=len(batch),
                        )
                        self._stats['errors'] += 1
                        break
                else:
                    # Non-retryable error
                    logger.error(
                        "export_failed_non_retryable_optimized",
                        status=e.response.status_code,
                        count=len(batch),
                    )
                    self._stats['errors'] += 1
                    break
                    
            except Exception as e:
                logger.error("export_error_optimized", error=str(e), attempt=attempt + 1)
                self._stats['errors'] += 1
                if attempt < self.max_retries:
                    await asyncio.sleep(2**attempt)
                else:
                    break
    
    def _create_otlp_request(self, batch: List[LogRecord]) -> ExportLogsServiceRequest:
        """Create OTLP ExportLogsServiceRequest efficiently."""
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
            log_records=batch,
        )
        
        # Create resource logs
        resource_logs = ResourceLogs(
            resource=resource,
            scope_logs=[scope_logs],
        )
        
        return ExportLogsServiceRequest(resource_logs=[resource_logs])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get exporter statistics."""
        with self._lock:
            batch_size = len(self.batch)
        
        return {
            **self._stats,
            'current_batch_size': batch_size,
            'cache_stats': get_signature_cache().get_stats(),
            'memory_pool_stats': self.memory_pool.get_stats(),
        }
