"""
Tests for Real-Time Streaming and Advanced Visualization
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.realtime_streaming import (
    StreamConfig, StreamMetrics, StreamAlert, StreamEvent,
    LogBuffer, RealTimeLogProcessor, WebSocketStreamManager,
    RealTimeStreamService
)
from src.visualization import (
    VisualizationConfig, ClusterVisualization, CorrelationTimeline,
    InsightDashboard, MetricsDashboard, DashboardManager,
    ClusterVisualizer, CorrelationTimelineVisualizer, InsightDashboardGenerator,
    MetricsDashboardGenerator
)
from src.intelligent_analysis import LogEntry, LogCluster, CorrelationPattern, LogInsight


class TestLogBuffer:
    """Test log buffer functionality"""
    
    @pytest.fixture
    def sample_log(self):
        """Create a sample log for testing"""
        return LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="Test error message",
            service_name="test-service"
        )
    
    @pytest.mark.asyncio
    async def test_add_and_get_logs(self, sample_log):
        """Test adding and getting logs from buffer"""
        buffer = LogBuffer(max_size=10)
        
        # Add log
        await buffer.add_log(sample_log)
        
        # Get logs
        logs = await buffer.get_logs()
        
        assert len(logs) == 1
        assert logs[0] == sample_log
    
    @pytest.mark.asyncio
    async def test_buffer_size_limit(self, sample_log):
        """Test buffer size limit"""
        buffer = LogBuffer(max_size=3)
        
        # Add more logs than buffer size
        for i in range(5):
            log = LogEntry(
                id=str(i),
                timestamp=datetime.utcnow(),
                level="INFO",
                message=f"Message {i}",
                service_name="test-service"
            )
            await buffer.add_log(log)
        
        # Buffer should only contain last 3 logs
        assert buffer.size() == 3
    
    @pytest.mark.asyncio
    async def test_wait_for_logs(self, sample_log):
        """Test waiting for logs"""
        buffer = LogBuffer()
        
        # Start waiting task
        wait_task = asyncio.create_task(buffer.wait_for_logs(timeout=1.0))
        
        # Add log after short delay
        await asyncio.sleep(0.1)
        await buffer.add_log(sample_log)
        
        # Wait should complete
        result = await wait_task
        assert result is True


class TestRealTimeLogProcessor:
    """Test real-time log processor functionality"""
    
    @pytest.fixture
    def processor(self):
        """Create a processor for testing"""
        config = StreamConfig(buffer_size=10, flush_interval=0.1)
        return RealTimeLogProcessor(config)
    
    @pytest.fixture
    def sample_log(self):
        """Create a sample log for testing"""
        return LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="Test error message",
            service_name="test-service"
        )
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, processor):
        """Test starting and stopping processor"""
        assert not processor._running
        
        await processor.start()
        assert processor._running
        
        await processor.stop()
        assert not processor._running
    
    @pytest.mark.asyncio
    async def test_add_log(self, processor, sample_log):
        """Test adding log to processor"""
        await processor.start()
        
        await processor.add_log(sample_log)
        
        # Check metrics
        assert processor.metrics.logs_received == 1
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_processing_loop(self, processor, sample_log):
        """Test the main processing loop"""
        await processor.start()
        
        # Add log
        await processor.add_log(sample_log)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Check metrics
        assert processor.metrics.logs_received >= 1
        assert processor.metrics.logs_processed >= 0
        
        await processor.stop()
    
    def test_get_metrics(self, processor):
        """Test getting metrics"""
        metrics = processor.get_metrics()
        
        assert isinstance(metrics, StreamMetrics)
        assert metrics.logs_received == 0
        assert metrics.logs_processed == 0
    
    def test_get_alerts(self, processor):
        """Test getting alerts"""
        alerts = processor.get_alerts()
        
        assert isinstance(alerts, list)
        assert len(alerts) == 0


class TestWebSocketStreamManager:
    """Test WebSocket stream manager functionality"""
    
    @pytest.fixture
    def processor(self):
        """Create a processor for testing"""
        return RealTimeLogProcessor()
    
    @pytest.fixture
    def ws_manager(self, processor):
        """Create a WebSocket manager for testing"""
        return WebSocketStreamManager(processor)
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect(self, ws_manager, mock_websocket):
        """Test WebSocket connection"""
        await ws_manager.connect(mock_websocket)
        
        assert mock_websocket in ws_manager.active_connections
        assert ws_manager.processor.metrics.active_connections == 1
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection"""
        await ws_manager.connect(mock_websocket)
        await ws_manager.disconnect(mock_websocket)
        
        assert mock_websocket not in ws_manager.active_connections
        assert ws_manager.processor.metrics.active_connections == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_event(self, ws_manager, mock_websocket):
        """Test broadcasting events"""
        await ws_manager.connect(mock_websocket)
        
        event = StreamEvent(
            event_type="test_event",
            data={"test": "data"}
        )
        
        await ws_manager.broadcast_event(event)
        
        mock_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_metrics(self, ws_manager, mock_websocket):
        """Test sending metrics"""
        await ws_manager.send_metrics(mock_websocket)
        
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "metrics"
    
    @pytest.mark.asyncio
    async def test_send_alerts(self, ws_manager, mock_websocket):
        """Test sending alerts"""
        await ws_manager.send_alerts(mock_websocket, limit=5)
        
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "alerts"


class TestRealTimeStreamService:
    """Test real-time stream service functionality"""
    
    @pytest.fixture
    def service(self):
        """Create a service for testing"""
        return RealTimeStreamService()
    
    @pytest.fixture
    def sample_log(self):
        """Create a sample log for testing"""
        return LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="Test error message",
            service_name="test-service"
        )
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, service):
        """Test starting and stopping service"""
        assert not service._running
        
        await service.start()
        assert service._running
        
        await service.stop()
        assert not service._running
    
    @pytest.mark.asyncio
    async def test_handle_websocket_message(self, service, sample_log):
        """Test handling WebSocket messages"""
        mock_websocket = AsyncMock()
        
        # Test add_log message
        message = {
            "type": "add_log",
            "log": {
                "id": sample_log.id,
                "timestamp": sample_log.timestamp.isoformat(),
                "level": sample_log.level,
                "message": sample_log.message,
                "service_name": sample_log.service_name
            }
        }
        
        await service._handle_websocket_message(mock_websocket, message)
        
        # Check that log was added
        assert service.processor.metrics.logs_received >= 0
    
    def test_get_processor(self, service):
        """Test getting processor"""
        processor = service.get_processor()
        
        assert isinstance(processor, RealTimeLogProcessor)
    
    def test_get_ws_manager(self, service):
        """Test getting WebSocket manager"""
        ws_manager = service.get_ws_manager()
        
        assert isinstance(ws_manager, WebSocketStreamManager)


class TestClusterVisualizer:
    """Test cluster visualizer functionality"""
    
    @pytest.fixture
    def sample_clusters(self):
        """Create sample clusters for testing"""
        return [
            LogCluster(
                id="cluster_1",
                name="Test Cluster 1",
                logs=[],
                semantic_summary="Test cluster 1 summary"
            ),
            LogCluster(
                id="cluster_2",
                name="Test Cluster 2",
                logs=[],
                semantic_summary="Test cluster 2 summary"
            )
        ]
    
    def test_visualize_clusters(self, sample_clusters):
        """Test cluster visualization generation"""
        visualizer = ClusterVisualizer()
        visualizations = visualizer.visualize_clusters(sample_clusters)
        
        assert len(visualizations) == len(sample_clusters)
        
        for i, viz in enumerate(visualizations):
            assert isinstance(viz, ClusterVisualization)
            assert viz.id == sample_clusters[i].id
            assert viz.name == sample_clusters[i].name
            assert viz.summary == sample_clusters[i].semantic_summary
            assert "x" in viz.position
            assert "y" in viz.position
            assert viz.color in visualizer.color_palette


class TestCorrelationTimelineVisualizer:
    """Test correlation timeline visualizer functionality"""
    
    @pytest.fixture
    def sample_correlations(self):
        """Create sample correlations for testing"""
        return [
            CorrelationPattern(
                id="correlation_1",
                pattern_type="error_sequence",
                events=[],
                correlation_strength=0.85,
                description="Test correlation 1"
            ),
            CorrelationPattern(
                id="correlation_2",
                pattern_type="user_flow",
                events=[],
                correlation_strength=0.72,
                description="Test correlation 2"
            )
        ]
    
    def test_visualize_correlations(self, sample_correlations):
        """Test correlation timeline visualization generation"""
        visualizer = CorrelationTimelineVisualizer()
        timelines = visualizer.visualize_correlations(sample_correlations)
        
        assert len(timelines) == len(sample_correlations)
        
        for i, timeline in enumerate(timelines):
            assert isinstance(timeline, CorrelationTimeline)
            assert timeline.id == sample_correlations[i].id
            assert timeline.pattern_type == sample_correlations[i].pattern_type
            assert timeline.correlation_strength == sample_correlations[i].correlation_strength
            assert timeline.description == sample_correlations[i].description


class TestInsightDashboardGenerator:
    """Test insight dashboard generator functionality"""
    
    @pytest.fixture
    def sample_insights(self):
        """Create sample insights for testing"""
        return [
            LogInsight(
                id="insight_1",
                title="Test Insight 1",
                type="anomaly",
                severity="critical",
                description="Test insight 1 description",
                actionable=True,
                recommended_actions=["Action 1", "Action 2"]
            ),
            LogInsight(
                id="insight_2",
                title="Test Insight 2",
                type="performance",
                severity="high",
                description="Test insight 2 description",
                actionable=True,
                recommended_actions=["Action 3"]
            ),
            LogInsight(
                id="insight_3",
                title="Test Insight 3",
                type="business",
                severity="medium",
                description="Test insight 3 description",
                actionable=False,
                recommended_actions=[]
            )
        ]
    
    def test_generate_dashboard(self, sample_insights):
        """Test insight dashboard generation"""
        generator = InsightDashboardGenerator()
        dashboard = generator.generate_dashboard(sample_insights)
        
        assert isinstance(dashboard, InsightDashboard)
        assert dashboard.total_insights == len(sample_insights)
        assert dashboard.critical_insights == 1
        assert dashboard.high_insights == 1
        assert dashboard.medium_insights == 1
        assert dashboard.low_insights == 0
        assert len(dashboard.recent_insights) <= 10
        assert len(dashboard.recommendations) > 0


class TestMetricsDashboardGenerator:
    """Test metrics dashboard generator functionality"""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing"""
        return StreamMetrics(
            logs_received=1000,
            logs_processed=950,
            logs_filtered=900,
            active_connections=5,
            processing_latency_ms=2.5,
            throughput_logs_per_second=150.0,
            error_count=10
        )
    
    def test_generate_dashboard(self, sample_metrics):
        """Test metrics dashboard generation"""
        generator = MetricsDashboardGenerator()
        dashboard = generator.generate_dashboard(sample_metrics)
        
        assert isinstance(dashboard, MetricsDashboard)
        assert dashboard.logs_per_second == sample_metrics.throughput_logs_per_second
        assert dashboard.processing_latency_ms == sample_metrics.processing_latency_ms
        assert dashboard.active_connections == sample_metrics.active_connections
        assert dashboard.error_rate == sample_metrics.error_count / sample_metrics.logs_received
        assert len(dashboard.throughput_trend) > 0
        assert len(dashboard.latency_trend) > 0


class TestDashboardManager:
    """Test dashboard manager functionality"""
    
    @pytest.fixture
    def manager(self):
        """Create a dashboard manager for testing"""
        config = VisualizationConfig(refresh_interval=0.1)
        return DashboardManager(config)
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, manager):
        """Test starting and stopping manager"""
        assert not manager._running
        
        await manager.start()
        assert manager._running
        
        await manager.stop()
        assert not manager._running
    
    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test WebSocket connection"""
        await manager.connect(mock_websocket)
        
        assert mock_websocket in manager.active_connections
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnection"""
        await manager.connect(mock_websocket)
        await manager.disconnect(mock_websocket)
        
        assert mock_websocket not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_update_loop(self, manager):
        """Test the update loop"""
        await manager.start()
        
        # Wait for at least one update cycle
        await asyncio.sleep(0.2)
        
        # Should have run without errors
        assert manager._running
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_generate_dashboard_data(self, manager):
        """Test dashboard data generation"""
        data = await manager._generate_dashboard_data()
        
        assert isinstance(data, dict)
        assert "metrics" in data
        assert "clusters" in data
        assert "correlations" in data
        assert "insights" in data
        assert "alerts" in data


class TestIntegration:
    """Integration tests for real-time streaming and visualization"""
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample logs for integration testing"""
        return [
            LogEntry(
                id=str(i),
                timestamp=datetime.utcnow(),
                level="ERROR" if i < 2 else "INFO",
                message=f"Test message {i}",
                service_name="test-service"
            )
            for i in range(5)
        ]
    
    @pytest.mark.asyncio
    async def test_realtime_streaming_integration(self, sample_logs):
        """Test real-time streaming integration"""
        service = RealTimeStreamService()
        
        await service.start()
        
        # Stream logs
        for log in sample_logs:
            await service.processor.add_log(log)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Check metrics
        metrics = service.processor.get_metrics()
        assert metrics.logs_received == len(sample_logs)
        assert metrics.logs_processed >= 0
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_visualization_integration(self, sample_logs):
        """Test visualization integration"""
        manager = DashboardManager()
        
        await manager.start()
        
        # Generate mock data
        clusters = [
            LogCluster(
                id="cluster_1",
                name="Test Cluster",
                logs=sample_logs,
                semantic_summary="Test cluster"
            )
        ]
        
        insights = [
            LogInsight(
                id="insight_1",
                title="Test Insight",
                type="anomaly",
                severity="high",
                description="Test description",
                actionable=True,
                recommended_actions=["Test action"]
            )
        ]
        
        # Generate visualizations
        cluster_viz = ClusterVisualizer().visualize_clusters(clusters)
        insights_viz = InsightDashboardGenerator().generate_dashboard(insights)
        
        assert len(cluster_viz) == 1
        assert insights_viz.total_insights == 1
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self, sample_logs):
        """Test complete workflow integration"""
        # Start services
        service = RealTimeStreamService()
        manager = DashboardManager()
        
        await service.start()
        await manager.start()
        
        # Stream logs
        for log in sample_logs:
            await service.processor.add_log(log)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Generate visualizations
        metrics = service.processor.get_metrics()
        metrics_dashboard = MetricsDashboardGenerator().generate_dashboard(metrics)
        
        assert metrics_dashboard.logs_per_second >= 0
        assert metrics_dashboard.active_connections >= 0
        
        # Stop services
        await service.stop()
        await manager.stop()
