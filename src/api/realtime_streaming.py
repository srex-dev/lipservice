"""
Real-Time Streaming API endpoints
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.realtime_streaming import (
    StreamConfig, StreamMetrics, StreamAlert, StreamEvent,
    RealTimeStreamService, LogEntry
)

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime-streaming"])

# Global streaming service instance
_streaming_service: Optional[RealTimeStreamService] = None


def get_streaming_service() -> RealTimeStreamService:
    """Get or create the global streaming service"""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = RealTimeStreamService()
    return _streaming_service


# Data Models
class StreamStatus(BaseModel):
    """Streaming service status"""
    running: bool
    active_connections: int
    logs_received: int
    logs_processed: int
    throughput_logs_per_second: float
    last_updated: datetime


class StreamConfiguration(BaseModel):
    """Streaming configuration"""
    buffer_size: int = Field(default=1000, ge=1, le=10000)
    flush_interval: float = Field(default=1.0, ge=0.1, le=60.0)
    max_connections: int = Field(default=100, ge=1, le=1000)
    enable_compression: bool = Field(default=True)
    enable_batching: bool = Field(default=True)
    batch_size: int = Field(default=100, ge=1, le=1000)


class LogStreamRequest(BaseModel):
    """Request to stream logs"""
    logs: List[LogEntry]
    batch_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamResponse(BaseModel):
    """Response from streaming operations"""
    success: bool
    message: str
    logs_processed: int
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


# API Endpoints
@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming.
    
    Clients can:
    - Send logs for real-time processing
    - Receive live insights and alerts
    - Monitor streaming metrics
    - Get real-time updates
    """
    service = get_streaming_service()
    
    # Start service if not running
    if not service._running:
        await service.start()
    
    await service.handle_websocket(websocket)


@router.post("/start", response_model=StreamResponse)
async def start_streaming(config: StreamConfiguration = None):
    """
    Start the real-time streaming service.
    """
    try:
        service = get_streaming_service()
        
        if config:
            # Update configuration
            stream_config = StreamConfig(**config.dict())
            service.config = stream_config
        
        if not service._running:
            await service.start()
        
        return StreamResponse(
            success=True,
            message="Real-time streaming service started",
            logs_processed=0,
            processing_time_ms=0.0,
            metadata={
                "config": service.config.dict(),
                "started_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start streaming: {str(e)}")


@router.post("/stop", response_model=StreamResponse)
async def stop_streaming():
    """
    Stop the real-time streaming service.
    """
    try:
        service = get_streaming_service()
        
        if service._running:
            await service.stop()
        
        return StreamResponse(
            success=True,
            message="Real-time streaming service stopped",
            logs_processed=service.processor.metrics.logs_processed,
            processing_time_ms=0.0,
            metadata={
                "stopped_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop streaming: {str(e)}")


@router.post("/logs", response_model=StreamResponse)
async def stream_logs(request: LogStreamRequest):
    """
    Stream logs for real-time processing.
    """
    try:
        service = get_streaming_service()
        
        if not service._running:
            await service.start()
        
        start_time = datetime.utcnow()
        
        # Add logs to processor
        for log in request.logs:
            await service.processor.add_log(log)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return StreamResponse(
            success=True,
            message=f"Streamed {len(request.logs)} logs",
            logs_processed=len(request.logs),
            processing_time_ms=processing_time,
            metadata={
                "batch_id": request.batch_id,
                "streamed_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream logs: {str(e)}")


@router.get("/status", response_model=StreamStatus)
async def get_streaming_status():
    """
    Get the current status of the streaming service.
    """
    try:
        service = get_streaming_service()
        metrics = service.processor.get_metrics()
        
        return StreamStatus(
            running=service._running,
            active_connections=metrics.active_connections,
            logs_received=metrics.logs_received,
            logs_processed=metrics.logs_processed,
            throughput_logs_per_second=metrics.throughput_logs_per_second,
            last_updated=metrics.last_updated
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/metrics", response_model=StreamMetrics)
async def get_streaming_metrics():
    """
    Get detailed streaming metrics.
    """
    try:
        service = get_streaming_service()
        return service.processor.get_metrics()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/alerts", response_model=List[StreamAlert])
async def get_streaming_alerts(limit: int = 50):
    """
    Get recent streaming alerts.
    """
    try:
        service = get_streaming_service()
        alerts = service.processor.get_alerts(limit)
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge a streaming alert.
    """
    try:
        service = get_streaming_service()
        
        # Find and acknowledge alert
        for alert in service.processor.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                break
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"success": True, "message": "Alert acknowledged"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.get("/events")
async def get_recent_events(limit: int = 100):
    """
    Get recent streaming events.
    """
    try:
        service = get_streaming_service()
        
        # In a real implementation, you'd store events in a database
        # For now, return a mock response
        events = [
            {
                "event_type": "log_received",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"log_count": 1},
                "metadata": {}
            }
        ]
        
        return {"events": events[:limit]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@router.post("/configure")
async def configure_streaming(config: StreamConfiguration):
    """
    Configure the streaming service.
    """
    try:
        service = get_streaming_service()
        
        # Update configuration
        stream_config = StreamConfig(**config.dict())
        service.config = stream_config
        
        # Restart service with new configuration if running
        if service._running:
            await service.stop()
            await service.start()
        
        return {
            "success": True,
            "message": "Streaming configuration updated",
            "config": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure streaming: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for real-time streaming service"""
    try:
        service = get_streaming_service()
        metrics = service.processor.get_metrics()
        
        return {
            "status": "healthy" if service._running else "stopped",
            "service": "realtime-streaming",
            "running": service._running,
            "active_connections": metrics.active_connections,
            "logs_processed": metrics.logs_processed,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "realtime-streaming",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
