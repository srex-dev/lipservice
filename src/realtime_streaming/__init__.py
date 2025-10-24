"""
Real-Time Log Streaming System

This module provides real-time log ingestion, processing, and analysis
capabilities for LipService.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator, Callable
from uuid import uuid4

import websockets
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.intelligent_analysis import LogEntry, IntelligentLogAnalyzer, LogInsight
from src.adaptive_filtering import AdaptiveLogFilter, FilterContext, SamplingDecision


class StreamConfig(BaseModel):
    """Configuration for log streaming"""
    buffer_size: int = Field(default=1000, ge=1, le=10000)
    flush_interval: float = Field(default=1.0, ge=0.1, le=60.0)
    max_connections: int = Field(default=100, ge=1, le=1000)
    enable_compression: bool = Field(default=True)
    enable_batching: bool = Field(default=True)
    batch_size: int = Field(default=100, ge=1, le=1000)


class StreamMetrics(BaseModel):
    """Real-time streaming metrics"""
    logs_received: int = Field(default=0)
    logs_processed: int = Field(default=0)
    logs_filtered: int = Field(default=0)
    active_connections: int = Field(default=0)
    processing_latency_ms: float = Field(default=0.0)
    throughput_logs_per_second: float = Field(default=0.0)
    error_count: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class StreamAlert(BaseModel):
    """Real-time alert"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str  # critical, warning, info
    title: str
    message: str
    severity: str  # critical, high, medium, low
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = Field(default=False)


class StreamEvent(BaseModel):
    """Real-time stream event"""
    event_type: str  # log_received, log_processed, insight_generated, alert_triggered
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogBuffer:
    """Thread-safe log buffer for streaming"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: List[LogEntry] = []
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
    
    async def add_log(self, log: LogEntry) -> None:
        """Add log to buffer"""
        async with self._condition:
            self.buffer.append(log)
            
            # Remove oldest logs if buffer is full
            while len(self.buffer) > self.max_size:
                self.buffer.pop(0)
            
            self._condition.notify_all()
    
    async def get_logs(self, max_count: int = None) -> List[LogEntry]:
        """Get logs from buffer"""
        async with self._condition:
            if max_count is None:
                max_count = len(self.buffer)
            
            logs = self.buffer[:max_count]
            self.buffer = self.buffer[max_count:]
            return logs
    
    async def wait_for_logs(self, timeout: float = None) -> bool:
        """Wait for logs to be available"""
        async with self._condition:
            if not self.buffer:
                await self._condition.wait(timeout)
            return len(self.buffer) > 0
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)


class RealTimeLogProcessor:
    """Real-time log processor with intelligent analysis"""
    
    def __init__(self, config: StreamConfig = None):
        self.config = config or StreamConfig()
        self.buffer = LogBuffer(self.config.buffer_size)
        self.analyzer = IntelligentLogAnalyzer()
        self.filter_engine = AdaptiveLogFilter()
        self.metrics = StreamMetrics()
        self.alerts: List[StreamAlert] = []
        self.event_handlers: List[Callable] = []
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the real-time processor"""
        if self._running:
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        await self._emit_event("processor_started", {"timestamp": datetime.utcnow()})
    
    async def stop(self) -> None:
        """Stop the real-time processor"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        await self._emit_event("processor_stopped", {"timestamp": datetime.utcnow()})
    
    async def add_log(self, log: LogEntry) -> None:
        """Add log for real-time processing"""
        await self.buffer.add_log(log)
        self.metrics.logs_received += 1
        await self._emit_event("log_received", {"log_id": log.id, "level": log.level})
    
    async def _processing_loop(self) -> None:
        """Main processing loop"""
        while self._running:
            try:
                # Wait for logs or timeout
                has_logs = await self.buffer.wait_for_logs(self.config.flush_interval)
                
                if has_logs:
                    await self._process_batch()
                
                # Update metrics
                await self._update_metrics()
                
            except Exception as e:
                self.metrics.error_count += 1
                await self._emit_event("processing_error", {"error": str(e)})
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _process_batch(self) -> None:
        """Process a batch of logs"""
        start_time = time.time()
        
        # Get logs from buffer
        logs = await self.buffer.get_logs(self.config.batch_size)
        if not logs:
            return
        
        # Process each log
        for log in logs:
            await self._process_single_log(log)
        
        # Update processing latency
        processing_time = (time.time() - start_time) * 1000
        self.metrics.processing_latency_ms = processing_time
        self.metrics.logs_processed += len(logs)
        
        await self._emit_event("batch_processed", {
            "log_count": len(logs),
            "processing_time_ms": processing_time
        })
    
    async def _process_single_log(self, log: LogEntry) -> None:
        """Process a single log entry"""
        try:
            # Apply adaptive filtering
            context = FilterContext(base_sampling_rate=0.1)
            decision = await self.filter_engine.adaptive_filter(log, context)
            
            if decision.sampling_rate > 0:
                # Log passed filtering - analyze it
                await self._analyze_log(log)
                self.metrics.logs_filtered += 1
                
                await self._emit_event("log_processed", {
                    "log_id": log.id,
                    "sampling_rate": decision.sampling_rate,
                    "reason": decision.reason
                })
            
        except Exception as e:
            self.metrics.error_count += 1
            await self._emit_event("log_processing_error", {
                "log_id": log.id,
                "error": str(e)
            })
    
    async def _analyze_log(self, log: LogEntry) -> None:
        """Analyze a single log for insights"""
        try:
            # Perform intelligent analysis
            result = await self.analyzer.analyze_logs(
                logs=[log],
                analysis_types=["insights"]
            )
            
            # Process insights
            for insight in result['insights']:
                await self._handle_insight(insight)
                
        except Exception as e:
            await self._emit_event("analysis_error", {
                "log_id": log.id,
                "error": str(e)
            })
    
    async def _handle_insight(self, insight: LogInsight) -> None:
        """Handle generated insights"""
        await self._emit_event("insight_generated", {
            "insight_id": insight.id,
            "type": insight.type,
            "severity": insight.severity,
            "title": insight.title
        })
        
        # Create alert for high-severity insights
        if insight.severity in ["critical", "high"]:
            alert = StreamAlert(
                type="insight",
                title=f"Insight: {insight.title}",
                message=insight.description,
                severity=insight.severity,
                metadata={
                    "insight_id": insight.id,
                    "confidence": insight.confidence,
                    "recommended_actions": insight.recommended_actions
                }
            )
            await self._add_alert(alert)
    
    async def _add_alert(self, alert: StreamAlert) -> None:
        """Add a new alert"""
        self.alerts.append(alert)
        
        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        await self._emit_event("alert_triggered", {
            "alert_id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "title": alert.title
        })
    
    async def _update_metrics(self) -> None:
        """Update streaming metrics"""
        current_time = time.time()
        
        # Calculate throughput (logs per second)
        if hasattr(self, '_last_metrics_time'):
            time_diff = current_time - self._last_metrics_time
            if time_diff > 0:
                logs_diff = self.metrics.logs_processed - getattr(self, '_last_processed_count', 0)
                self.metrics.throughput_logs_per_second = logs_diff / time_diff
        
        self._last_metrics_time = current_time
        self._last_processed_count = self.metrics.logs_processed
        self.metrics.last_updated = datetime.utcnow()
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit a stream event"""
        event = StreamEvent(
            event_type=event_type,
            data=data
        )
        
        # Notify all event handlers
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                # Don't let handler errors break the processor
                pass
    
    def add_event_handler(self, handler: Callable) -> None:
        """Add an event handler"""
        self.event_handlers.append(handler)
    
    def get_metrics(self) -> StreamMetrics:
        """Get current metrics"""
        return self.metrics
    
    def get_alerts(self, limit: int = 50) -> List[StreamAlert]:
        """Get recent alerts"""
        return self.alerts[-limit:] if self.alerts else []


class WebSocketStreamManager:
    """Manages WebSocket connections for real-time streaming"""
    
    def __init__(self, processor: RealTimeLogProcessor):
        self.processor = processor
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        async with self._lock:
            self.active_connections.append(websocket)
            self.processor.metrics.active_connections = len(self.active_connections)
        
        await self._send_welcome_message(websocket)
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket connection"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                self.processor.metrics.active_connections = len(self.active_connections)
    
    async def broadcast_event(self, event: StreamEvent) -> None:
        """Broadcast event to all connected clients"""
        if not self.active_connections:
            return
        
        message = {
            "type": "stream_event",
            "event": event.dict()
        }
        
        # Send to all connections
        disconnected = []
        async with self._lock:
            for websocket in self.active_connections:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception:
                    disconnected.append(websocket)
            
            # Remove disconnected connections
            for websocket in disconnected:
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
            
            self.processor.metrics.active_connections = len(self.active_connections)
    
    async def send_metrics(self, websocket: WebSocket) -> None:
        """Send current metrics to a specific client"""
        metrics = self.processor.get_metrics()
        message = {
            "type": "metrics",
            "metrics": metrics.dict()
        }
        await websocket.send_text(json.dumps(message, default=str))
    
    async def send_alerts(self, websocket: WebSocket, limit: int = 10) -> None:
        """Send recent alerts to a specific client"""
        alerts = self.processor.get_alerts(limit)
        message = {
            "type": "alerts",
            "alerts": [alert.dict() for alert in alerts]
        }
        await websocket.send_text(json.dumps(message, default=str))
    
    async def _send_welcome_message(self, websocket: WebSocket) -> None:
        """Send welcome message to new connection"""
        welcome = {
            "type": "welcome",
            "message": "Connected to LipService Real-Time Stream",
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": [
                "log_streaming",
                "real_time_analysis",
                "live_insights",
                "adaptive_filtering",
                "metrics_monitoring"
            ]
        }
        await websocket.send_text(json.dumps(welcome, default=str))


class KafkaStreamConsumer:
    """Kafka consumer for high-throughput log ingestion"""
    
    def __init__(self, processor: RealTimeLogProcessor, kafka_config: Dict[str, Any] = None):
        self.processor = processor
        self.kafka_config = kafka_config or {
            "bootstrap_servers": ["localhost:9092"],
            "group_id": "lipservice-consumer",
            "auto_offset_reset": "latest"
        }
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start Kafka consumer"""
        if self._running:
            return
        
        self._running = True
        self._consumer_task = asyncio.create_task(self._consume_loop())
    
    async def stop(self) -> None:
        """Stop Kafka consumer"""
        self._running = False
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
    
    async def _consume_loop(self) -> None:
        """Main consumption loop"""
        try:
            # Mock Kafka consumer (in production, use aiokafka)
            while self._running:
                # Simulate receiving logs from Kafka
                await asyncio.sleep(0.1)
                
                # In production, this would be:
                # async for message in kafka_consumer:
                #     log_data = json.loads(message.value)
                #     log = LogEntry(**log_data)
                #     await self.processor.add_log(log)
                
        except Exception as e:
            await self.processor._emit_event("kafka_error", {"error": str(e)})


class RealTimeStreamService:
    """Main service for real-time log streaming"""
    
    def __init__(self, config: StreamConfig = None):
        self.config = config or StreamConfig()
        self.processor = RealTimeLogProcessor(self.config)
        self.ws_manager = WebSocketStreamManager(self.processor)
        self.kafka_consumer = KafkaStreamConsumer(self.processor)
        self._running = False
    
    async def start(self) -> None:
        """Start the streaming service"""
        if self._running:
            return
        
        self._running = True
        
        # Start processor
        await self.processor.start()
        
        # Start Kafka consumer
        await self.kafka_consumer.start()
        
        # Add event handler for WebSocket broadcasting
        self.processor.add_event_handler(self.ws_manager.broadcast_event)
    
    async def stop(self) -> None:
        """Stop the streaming service"""
        self._running = False
        
        await self.processor.stop()
        await self.kafka_consumer.stop()
    
    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle WebSocket connection"""
        await self.ws_manager.connect(websocket)
        
        try:
            while True:
                # Handle incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await self._handle_websocket_message(websocket, message)
                
        except WebSocketDisconnect:
            await self.ws_manager.disconnect(websocket)
        except Exception as e:
            await self.ws_manager.disconnect(websocket)
            await self.processor._emit_event("websocket_error", {"error": str(e)})
    
    async def _handle_websocket_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message"""
        message_type = message.get("type")
        
        if message_type == "get_metrics":
            await self.ws_manager.send_metrics(websocket)
        elif message_type == "get_alerts":
            limit = message.get("limit", 10)
            await self.ws_manager.send_alerts(websocket, limit)
        elif message_type == "add_log":
            # Add log for processing
            log_data = message.get("log")
            if log_data:
                log = LogEntry(**log_data)
                await self.processor.add_log(log)
        elif message_type == "ping":
            # Respond to ping
            pong = {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
            await websocket.send_text(json.dumps(pong, default=str))
    
    def get_processor(self) -> RealTimeLogProcessor:
        """Get the log processor"""
        return self.processor
    
    def get_ws_manager(self) -> WebSocketStreamManager:
        """Get the WebSocket manager"""
        return self.ws_manager
