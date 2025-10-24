"""
Advanced Visualization Dashboard System

This module provides interactive visualizations for log analysis,
clustering, correlations, and real-time insights.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.intelligent_analysis import LogCluster, CorrelationPattern, LogInsight, LogEntry
from src.realtime_streaming import StreamMetrics, StreamAlert


class VisualizationConfig(BaseModel):
    """Configuration for visualizations"""
    refresh_interval: float = Field(default=1.0, ge=0.1, le=60.0)
    max_data_points: int = Field(default=1000, ge=10, le=10000)
    enable_animations: bool = Field(default=True)
    theme: str = Field(default="dark", pattern="^(dark|light)$")
    chart_types: List[str] = Field(default=["line", "bar", "scatter", "heatmap"])


class ClusterVisualization(BaseModel):
    """Cluster visualization data"""
    id: str
    name: str
    size: int
    color: str
    position: Dict[str, float]  # x, y coordinates
    logs: List[Dict[str, Any]]
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CorrelationTimeline(BaseModel):
    """Temporal correlation timeline data"""
    id: str
    pattern_type: str
    events: List[Dict[str, Any]]
    time_range: Dict[str, str]  # start, end timestamps
    correlation_strength: float
    description: str
    visualization_data: Dict[str, Any] = Field(default_factory=dict)


class InsightDashboard(BaseModel):
    """Insights dashboard data"""
    total_insights: int
    critical_insights: int
    high_insights: int
    medium_insights: int
    low_insights: int
    recent_insights: List[Dict[str, Any]]
    trend_data: List[Dict[str, Any]]
    recommendations: List[str]


class MetricsDashboard(BaseModel):
    """Real-time metrics dashboard data"""
    logs_per_second: float
    processing_latency_ms: float
    error_rate: float
    active_connections: int
    memory_usage: float
    cpu_usage: float
    throughput_trend: List[Dict[str, Any]]
    latency_trend: List[Dict[str, Any]]


class ChartData(BaseModel):
    """Generic chart data structure"""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = Field(default_factory=dict)


class VisualizationRequest(BaseModel):
    """Request for visualization data"""
    visualization_type: str  # cluster, correlation, insights, metrics
    time_range: Optional[Dict[str, str]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class VisualizationResponse(BaseModel):
    """Response with visualization data"""
    visualization_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DashboardManager:
    """Manages dashboard visualizations and real-time updates"""
    
    def __init__(self, config: VisualizationConfig = None):
        self.config = config or VisualizationConfig()
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the dashboard manager"""
        if self._running:
            return
        
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def stop(self) -> None:
        """Stop the dashboard manager"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def connect(self, websocket: WebSocket) -> None:
        """Connect a new dashboard client"""
        await websocket.accept()
        
        async with self._lock:
            self.active_connections.append(websocket)
        
        await self._send_welcome_message(websocket)
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a dashboard client"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def _update_loop(self) -> None:
        """Main update loop for real-time dashboard updates"""
        while self._running:
            try:
                if self.active_connections:
                    await self._broadcast_updates()
                
                await asyncio.sleep(self.config.refresh_interval)
                
            except Exception as e:
                # Log error and continue
                await asyncio.sleep(1)
    
    async def _broadcast_updates(self) -> None:
        """Broadcast updates to all connected clients"""
        if not self.active_connections:
            return
        
        # Generate update data
        update_data = {
            "type": "dashboard_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": await self._generate_dashboard_data()
        }
        
        # Send to all connections
        disconnected = []
        async with self._lock:
            for websocket in self.active_connections:
                try:
                    await websocket.send_text(json.dumps(update_data, default=str))
                except Exception:
                    disconnected.append(websocket)
            
            # Remove disconnected connections
            for websocket in disconnected:
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    async def _generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        return {
            "metrics": await self._generate_metrics_data(),
            "clusters": await self._generate_cluster_data(),
            "correlations": await self._generate_correlation_data(),
            "insights": await self._generate_insights_data(),
            "alerts": await self._generate_alerts_data()
        }
    
    async def _generate_metrics_data(self) -> Dict[str, Any]:
        """Generate metrics visualization data"""
        # Mock metrics data (in production, get from actual metrics)
        return {
            "logs_per_second": 150.5,
            "processing_latency_ms": 2.3,
            "error_rate": 0.05,
            "active_connections": len(self.active_connections),
            "memory_usage": 0.65,
            "cpu_usage": 0.45,
            "throughput_trend": [
                {"timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(), "value": 100 + i * 10}
                for i in range(10, 0, -1)
            ],
            "latency_trend": [
                {"timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(), "value": 1.5 + i * 0.1}
                for i in range(10, 0, -1)
            ]
        }
    
    async def _generate_cluster_data(self) -> List[Dict[str, Any]]:
        """Generate cluster visualization data"""
        # Mock cluster data (in production, get from actual analysis)
        return [
            {
                "id": "cluster_1",
                "name": "Database Errors",
                "size": 45,
                "color": "#ff4444",
                "position": {"x": 0.2, "y": 0.3},
                "logs": [
                    {"id": "log_1", "message": "Connection timeout", "level": "ERROR"},
                    {"id": "log_2", "message": "Query failed", "level": "ERROR"}
                ],
                "summary": "Database connection and query errors",
                "metadata": {"error_count": 45, "services": ["db-service"]}
            },
            {
                "id": "cluster_2", 
                "name": "User Authentication",
                "size": 120,
                "color": "#4444ff",
                "position": {"x": 0.7, "y": 0.6},
                "logs": [
                    {"id": "log_3", "message": "User login successful", "level": "INFO"},
                    {"id": "log_4", "message": "User logout", "level": "INFO"}
                ],
                "summary": "User authentication events",
                "metadata": {"success_count": 100, "failure_count": 20, "services": ["auth-service"]}
            }
        ]
    
    async def _generate_correlation_data(self) -> List[Dict[str, Any]]:
        """Generate correlation timeline data"""
        # Mock correlation data
        return [
            {
                "id": "correlation_1",
                "pattern_type": "error_sequence",
                "events": [
                    {"timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), "type": "ERROR", "message": "Database timeout"},
                    {"timestamp": (datetime.utcnow() - timedelta(minutes=4)).isoformat(), "type": "ERROR", "message": "Connection failed"},
                    {"timestamp": (datetime.utcnow() - timedelta(minutes=3)).isoformat(), "type": "WARNING", "message": "High latency detected"}
                ],
                "time_range": {
                    "start": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "end": (datetime.utcnow() - timedelta(minutes=3)).isoformat()
                },
                "correlation_strength": 0.85,
                "description": "Database timeout leading to connection failures",
                "visualization_data": {
                    "timeline_points": [
                        {"x": 0, "y": 0.8, "label": "Database timeout"},
                        {"x": 1, "y": 0.9, "label": "Connection failed"},
                        {"x": 2, "y": 0.6, "label": "High latency"}
                    ]
                }
            }
        ]
    
    async def _generate_insights_data(self) -> Dict[str, Any]:
        """Generate insights dashboard data"""
        return {
            "total_insights": 15,
            "critical_insights": 2,
            "high_insights": 3,
            "medium_insights": 5,
            "low_insights": 5,
            "recent_insights": [
                {
                    "id": "insight_1",
                    "title": "High Error Rate Detected",
                    "type": "anomaly",
                    "severity": "critical",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                    "description": "Error rate increased by 200% in the last 5 minutes"
                },
                {
                    "id": "insight_2",
                    "title": "Performance Degradation",
                    "type": "performance",
                    "severity": "high",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "description": "Response time increased by 150%"
                }
            ],
            "trend_data": [
                {"timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(), "insights": 1 + i % 3}
                for i in range(20, 0, -1)
            ],
            "recommendations": [
                "Investigate database connection pool settings",
                "Review recent deployments for potential issues",
                "Consider scaling database resources",
                "Monitor error patterns for root cause analysis"
            ]
        }
    
    async def _generate_alerts_data(self) -> List[Dict[str, Any]]:
        """Generate alerts data"""
        return [
            {
                "id": "alert_1",
                "type": "critical",
                "title": "Database Connection Pool Exhausted",
                "message": "All database connections are in use",
                "severity": "critical",
                "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                "acknowledged": False,
                "metadata": {"service": "db-service", "connection_count": 100}
            },
            {
                "id": "alert_2",
                "type": "warning",
                "title": "High Memory Usage",
                "message": "Memory usage exceeded 85%",
                "severity": "high",
                "timestamp": (datetime.utcnow() - timedelta(minutes=3)).isoformat(),
                "acknowledged": True,
                "metadata": {"memory_usage": 0.87, "threshold": 0.85}
            }
        ]
    
    async def _send_welcome_message(self, websocket: WebSocket) -> None:
        """Send welcome message to new dashboard client"""
        welcome = {
            "type": "dashboard_welcome",
            "message": "Connected to LipService Dashboard",
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": [
                "real_time_metrics",
                "cluster_visualization", 
                "correlation_timeline",
                "insights_dashboard",
                "alerts_monitoring"
            ],
            "config": self.config.dict()
        }
        await websocket.send_text(json.dumps(welcome, default=str))


class ClusterVisualizer:
    """Specialized cluster visualization generator"""
    
    def __init__(self):
        self.color_palette = [
            "#ff4444", "#4444ff", "#44ff44", "#ffff44",
            "#ff44ff", "#44ffff", "#ff8844", "#8844ff"
        ]
    
    def visualize_clusters(self, clusters: List[LogCluster]) -> List[ClusterVisualization]:
        """Generate cluster visualization data"""
        visualizations = []
        
        for i, cluster in enumerate(clusters):
            # Calculate cluster position (simple 2D layout)
            x = (i % 3) * 0.3 + 0.1
            y = (i // 3) * 0.3 + 0.1
            
            # Prepare log data
            logs_data = []
            for log in cluster.logs[:10]:  # Limit to first 10 logs
                logs_data.append({
                    "id": log.id,
                    "message": log.message[:50] + "..." if len(log.message) > 50 else log.message,
                    "level": log.level,
                    "timestamp": log.timestamp.isoformat(),
                    "service": log.service_name
                })
            
            visualization = ClusterVisualization(
                id=cluster.id,
                name=cluster.name,
                size=len(cluster.logs),
                color=self.color_palette[i % len(self.color_palette)],
                position={"x": x, "y": y},
                logs=logs_data,
                summary=cluster.semantic_summary,
                metadata={
                    "log_count": len(cluster.logs),
                    "services": list(set(log.service_name for log in cluster.logs)),
                    "levels": list(set(log.level for log in cluster.logs))
                }
            )
            visualizations.append(visualization)
        
        return visualizations


class CorrelationTimelineVisualizer:
    """Specialized correlation timeline visualization generator"""
    
    def visualize_correlations(self, correlations: List[CorrelationPattern]) -> List[CorrelationTimeline]:
        """Generate correlation timeline visualization data"""
        timelines = []
        
        for correlation in correlations:
            # Prepare event data
            events_data = []
            for event in correlation.events:
                events_data.append({
                    "id": event.original_log.id,
                    "timestamp": event.original_log.timestamp.isoformat(),
                    "type": event.original_log.level,
                    "message": event.original_log.message[:50] + "..." if len(event.original_log.message) > 50 else event.original_log.message,
                    "service": event.original_log.service_name
                })
            
            # Calculate time range
            if events_data:
                timestamps = [event["timestamp"] for event in events_data]
                time_range = {
                    "start": min(timestamps),
                    "end": max(timestamps)
                }
            else:
                time_range = {"start": "", "end": ""}
            
            # Generate visualization data
            visualization_data = {
                "timeline_points": [
                    {
                        "x": i / max(len(events_data) - 1, 1),
                        "y": correlation.correlation_strength,
                        "label": event["message"],
                        "timestamp": event["timestamp"]
                    }
                    for i, event in enumerate(events_data)
                ]
            }
            
            timeline = CorrelationTimeline(
                id=correlation.id,
                pattern_type=correlation.pattern_type,
                events=events_data,
                time_range=time_range,
                correlation_strength=correlation.correlation_strength,
                description=correlation.description,
                visualization_data=visualization_data
            )
            timelines.append(timeline)
        
        return timelines


class InsightDashboardGenerator:
    """Specialized insights dashboard generator"""
    
    def generate_dashboard(self, insights: List[LogInsight]) -> InsightDashboard:
        """Generate insights dashboard data"""
        # Count insights by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for insight in insights:
            severity_counts[insight.severity] += 1
        
        # Get recent insights (last 10)
        recent_insights = sorted(insights, key=lambda x: x.generated_at, reverse=True)[:10]
        recent_data = []
        for insight in recent_insights:
            recent_data.append({
                "id": insight.id,
                "title": insight.title,
                "type": insight.type,
                "severity": insight.severity,
                "timestamp": insight.generated_at.isoformat(),
                "description": insight.description,
                "confidence": insight.confidence,
                "actionable": insight.actionable
            })
        
        # Generate trend data (mock for now)
        trend_data = [
            {"timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(), "insights": len([insight for insight in insights if insight.generated_at >= datetime.utcnow() - timedelta(hours=i)])}
            for i in range(24, 0, -1)
        ]
        
        # Extract recommendations
        recommendations = []
        for insight in insights:
            if insight.actionable and insight.recommended_actions:
                recommendations.extend(insight.recommended_actions)
        
        return InsightDashboard(
            total_insights=len(insights),
            critical_insights=severity_counts["critical"],
            high_insights=severity_counts["high"],
            medium_insights=severity_counts["medium"],
            low_insights=severity_counts["low"],
            recent_insights=recent_data,
            trend_data=trend_data,
            recommendations=list(set(recommendations))[:10]  # Unique recommendations, max 10
        )


class MetricsDashboardGenerator:
    """Specialized metrics dashboard generator"""
    
    def generate_dashboard(self, metrics: StreamMetrics) -> MetricsDashboard:
        """Generate metrics dashboard data"""
        # Calculate error rate
        error_rate = 0.0
        if metrics.logs_received > 0:
            error_rate = metrics.error_count / metrics.logs_received
        
        # Generate trend data (mock for now)
        throughput_trend = [
            {"timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(), "value": metrics.throughput_logs_per_second + (i % 3 - 1) * 10}
            for i in range(60, 0, -1)
        ]
        
        latency_trend = [
            {"timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(), "value": metrics.processing_latency_ms + (i % 2 - 0.5) * 2}
            for i in range(60, 0, -1)
        ]
        
        return MetricsDashboard(
            logs_per_second=metrics.throughput_logs_per_second,
            processing_latency_ms=metrics.processing_latency_ms,
            error_rate=error_rate,
            active_connections=metrics.active_connections,
            memory_usage=0.65,  # Mock data
            cpu_usage=0.45,     # Mock data
            throughput_trend=throughput_trend,
            latency_trend=latency_trend
        )
