"""
Advanced Visualization API endpoints
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.visualization import (
    VisualizationConfig, ClusterVisualization, CorrelationTimeline,
    InsightDashboard, MetricsDashboard, ChartData, DashboardManager,
    ClusterVisualizer, CorrelationTimelineVisualizer, InsightDashboardGenerator,
    MetricsDashboardGenerator
)
from src.intelligent_analysis import LogCluster, CorrelationPattern, LogInsight
from src.realtime_streaming import StreamMetrics

router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])

# Global dashboard manager instance
_dashboard_manager: Optional[DashboardManager] = None


def get_dashboard_manager() -> DashboardManager:
    """Get or create the global dashboard manager"""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager


# Data Models
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


class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    refresh_interval: float = Field(default=1.0, ge=0.1, le=60.0)
    max_data_points: int = Field(default=1000, ge=10, le=10000)
    enable_animations: bool = Field(default=True)
    theme: str = Field(default="dark", pattern="^(dark|light)$")
    chart_types: List[str] = Field(default=["line", "bar", "scatter", "heatmap"])


# API Endpoints
@router.websocket("/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Clients receive:
    - Real-time metrics updates
    - Live cluster visualizations
    - Correlation timeline updates
    - Insights dashboard data
    - Alert notifications
    """
    manager = get_dashboard_manager()
    
    # Start manager if not running
    if not manager._running:
        await manager.start()
    
    await manager.connect(websocket)
    
    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await _handle_dashboard_message(websocket, message)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        await manager.disconnect(websocket)
        # Log error


async def _handle_dashboard_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle incoming dashboard WebSocket message"""
    message_type = message.get("type")
    
    if message_type == "get_clusters":
        await _send_cluster_visualization(websocket)
    elif message_type == "get_correlations":
        await _send_correlation_timeline(websocket)
    elif message_type == "get_insights":
        await _send_insights_dashboard(websocket)
    elif message_type == "get_metrics":
        await _send_metrics_dashboard(websocket)
    elif message_type == "ping":
        pong = {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        await websocket.send_text(json.dumps(pong, default=str))


async def _send_cluster_visualization(websocket: WebSocket):
    """Send cluster visualization data"""
    # Mock cluster data (in production, get from actual analysis)
    clusters = [
        LogCluster(
            id="cluster_1",
            name="Database Errors",
            logs=[],
            semantic_summary="Database connection and query errors"
        ),
        LogCluster(
            id="cluster_2",
            name="User Authentication", 
            logs=[],
            semantic_summary="User authentication events"
        )
    ]
    
    visualizer = ClusterVisualizer()
    visualization_data = visualizer.visualize_clusters(clusters)
    
    message = {
        "type": "cluster_visualization",
        "data": [cluster.dict() for cluster in visualization_data],
        "timestamp": datetime.utcnow().isoformat()
    }
    await websocket.send_text(json.dumps(message, default=str))


async def _send_correlation_timeline(websocket: WebSocket):
    """Send correlation timeline data"""
    # Mock correlation data
    correlations = [
        CorrelationPattern(
            id="correlation_1",
            pattern_type="error_sequence",
            events=[],
            correlation_strength=0.85,
            description="Database timeout leading to connection failures"
        )
    ]
    
    visualizer = CorrelationTimelineVisualizer()
    timeline_data = visualizer.visualize_correlations(correlations)
    
    message = {
        "type": "correlation_timeline",
        "data": [timeline.dict() for timeline in timeline_data],
        "timestamp": datetime.utcnow().isoformat()
    }
    await websocket.send_text(json.dumps(message, default=str))


async def _send_insights_dashboard(websocket: WebSocket):
    """Send insights dashboard data"""
    # Mock insights data
    insights = [
        LogInsight(
            id="insight_1",
            title="High Error Rate Detected",
            type="anomaly",
            severity="critical",
            description="Error rate increased by 200% in the last 5 minutes",
            actionable=True,
            recommended_actions=["Investigate database connections", "Check recent deployments"]
        ),
        LogInsight(
            id="insight_2",
            title="Performance Degradation",
            type="performance", 
            severity="high",
            description="Response time increased by 150%",
            actionable=True,
            recommended_actions=["Scale resources", "Check system load"]
        )
    ]
    
    generator = InsightDashboardGenerator()
    dashboard_data = generator.generate_dashboard(insights)
    
    message = {
        "type": "insights_dashboard",
        "data": dashboard_data.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
    await websocket.send_text(json.dumps(message, default=str))


async def _send_metrics_dashboard(websocket: WebSocket):
    """Send metrics dashboard data"""
    # Mock metrics data
    metrics = StreamMetrics(
        logs_received=1000,
        logs_processed=950,
        logs_filtered=900,
        active_connections=5,
        processing_latency_ms=2.5,
        throughput_logs_per_second=150.0,
        error_count=10
    )
    
    generator = MetricsDashboardGenerator()
    dashboard_data = generator.generate_dashboard(metrics)
    
    message = {
        "type": "metrics_dashboard",
        "data": dashboard_data.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
    await websocket.send_text(json.dumps(message, default=str))


@router.post("/clusters", response_model=List[ClusterVisualization])
async def get_cluster_visualization(
    clusters: List[LogCluster],
    options: Dict[str, Any] = Field(default_factory=dict)
):
    """
    Generate cluster visualization data.
    """
    try:
        visualizer = ClusterVisualizer()
        visualization_data = visualizer.visualize_clusters(clusters)
        
        return visualization_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cluster visualization: {str(e)}")


@router.post("/correlations", response_model=List[CorrelationTimeline])
async def get_correlation_timeline(
    correlations: List[CorrelationPattern],
    options: Dict[str, Any] = Field(default_factory=dict)
):
    """
    Generate correlation timeline visualization data.
    """
    try:
        visualizer = CorrelationTimelineVisualizer()
        timeline_data = visualizer.visualize_correlations(correlations)
        
        return timeline_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate correlation timeline: {str(e)}")


@router.post("/insights", response_model=InsightDashboard)
async def get_insights_dashboard(
    insights: List[LogInsight],
    options: Dict[str, Any] = Field(default_factory=dict)
):
    """
    Generate insights dashboard data.
    """
    try:
        generator = InsightDashboardGenerator()
        dashboard_data = generator.generate_dashboard(insights)
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights dashboard: {str(e)}")


@router.post("/metrics", response_model=MetricsDashboard)
async def get_metrics_dashboard(
    metrics: StreamMetrics,
    options: Dict[str, Any] = Field(default_factory=dict)
):
    """
    Generate metrics dashboard data.
    """
    try:
        generator = MetricsDashboardGenerator()
        dashboard_data = generator.generate_dashboard(metrics)
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics dashboard: {str(e)}")


@router.post("/chart", response_model=ChartData)
async def generate_chart_data(
    chart_type: str,
    data: Dict[str, Any],
    options: Dict[str, Any] = Field(default_factory=dict)
):
    """
    Generate generic chart data for various visualization types.
    """
    try:
        # Generate chart data based on type
        if chart_type == "line":
            chart_data = ChartData(
                labels=[f"Point {i}" for i in range(10)],
                datasets=[{
                    "label": "Sample Data",
                    "data": [i * 10 for i in range(10)],
                    "borderColor": "#4444ff",
                    "backgroundColor": "rgba(68, 68, 255, 0.1)"
                }],
                options={
                    "responsive": True,
                    "scales": {
                        "y": {"beginAtZero": True}
                    }
                }
            )
        elif chart_type == "bar":
            chart_data = ChartData(
                labels=["Error", "Warning", "Info", "Debug"],
                datasets=[{
                    "label": "Log Levels",
                    "data": [45, 23, 120, 8],
                    "backgroundColor": ["#ff4444", "#ffaa44", "#4444ff", "#44ff44"]
                }],
                options={
                    "responsive": True,
                    "scales": {
                        "y": {"beginAtZero": True}
                    }
                }
            )
        elif chart_type == "scatter":
            chart_data = ChartData(
                labels=["Cluster 1", "Cluster 2", "Cluster 3"],
                datasets=[{
                    "label": "Log Clusters",
                    "data": [{"x": 0.2, "y": 0.3}, {"x": 0.7, "y": 0.6}, {"x": 0.4, "y": 0.8}],
                    "backgroundColor": ["#ff4444", "#4444ff", "#44ff44"]
                }],
                options={
                    "responsive": True,
                    "scales": {
                        "x": {"min": 0, "max": 1},
                        "y": {"min": 0, "max": 1}
                    }
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")
        
        return chart_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chart data: {str(e)}")


@router.post("/configure")
async def configure_dashboard(config: DashboardConfig):
    """
    Configure the dashboard settings.
    """
    try:
        manager = get_dashboard_manager()
        
        # Update configuration
        viz_config = VisualizationConfig(**config.dict())
        manager.config = viz_config
        
        return {
            "success": True,
            "message": "Dashboard configuration updated",
            "config": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure dashboard: {str(e)}")


@router.get("/status")
async def get_dashboard_status():
    """
    Get the current status of the dashboard.
    """
    try:
        manager = get_dashboard_manager()
        
        return {
            "running": manager._running,
            "active_connections": len(manager.active_connections),
            "config": manager.config.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard status: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for visualization service"""
    try:
        manager = get_dashboard_manager()
        
        return {
            "status": "healthy",
            "service": "visualization",
            "running": manager._running,
            "active_connections": len(manager.active_connections),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "visualization",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
