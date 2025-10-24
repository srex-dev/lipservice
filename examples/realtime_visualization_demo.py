"""
Comprehensive Demo: Real-Time Streaming & Advanced Visualization

This demo showcases the complete LipService platform with real-time
streaming and advanced visualization capabilities.
"""

import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import List

from src.intelligent_analysis import LogEntry, IntelligentLogAnalyzer
from src.adaptive_filtering import FilterContext, AdaptiveLogFilter
from src.realtime_streaming import RealTimeStreamService, StreamConfig
from src.visualization import DashboardManager, VisualizationConfig


async def create_demo_logs() -> List[LogEntry]:
    """Create demo logs for real-time streaming"""
    
    base_time = datetime.utcnow()
    
    logs = [
        # Critical errors - should trigger alerts
        LogEntry(
            id="1",
            timestamp=base_time,
            level="ERROR",
            message="Database connection pool exhausted - all connections in use",
            service_name="database-service",
            metadata={"connection_count": 100, "max_connections": 100}
        ),
        LogEntry(
            id="2",
            timestamp=base_time + timedelta(seconds=30),
            level="ERROR",
            message="Payment processing failed for transaction 12345",
            service_name="payment-service",
            metadata={"transaction_id": "12345", "amount": 99.99, "user_id": "user_67890"}
        ),
        
        # Warnings - should be monitored
        LogEntry(
            id="3",
            timestamp=base_time + timedelta(minutes=1),
            level="WARNING",
            message="High memory usage detected: 87%",
            service_name="monitoring-service",
            metadata={"memory_usage": 0.87, "threshold": 0.85}
        ),
        LogEntry(
            id="4",
            timestamp=base_time + timedelta(minutes=2),
            level="WARNING",
            message="API response time exceeded threshold: 3.2s",
            service_name="api-gateway",
            metadata={"response_time": 3.2, "threshold": 2.0}
        ),
        
        # Info logs - should be sampled
        LogEntry(
            id="5",
            timestamp=base_time + timedelta(minutes=3),
            level="INFO",
            message="User 11111 logged in successfully via OAuth",
            service_name="auth-service",
            metadata={"user_id": "11111", "login_method": "oauth", "ip": "192.168.1.100"}
        ),
        LogEntry(
            id="6",
            timestamp=base_time + timedelta(minutes=4),
            level="INFO",
            message="User 22222 logged in successfully via OAuth",
            service_name="auth-service",
            metadata={"user_id": "22222", "login_method": "oauth", "ip": "192.168.1.101"}
        ),
        LogEntry(
            id="7",
            timestamp=base_time + timedelta(minutes=5),
            level="INFO",
            message="Cache hit for key: user_profile_33333",
            service_name="cache-service",
            metadata={"cache_key": "user_profile_33333", "hit_rate": 0.95}
        ),
        
        # Debug logs - should be heavily sampled
        LogEntry(
            id="8",
            timestamp=base_time + timedelta(minutes=6),
            level="DEBUG",
            message="Processing request with ID: req-456",
            service_name="request-processor",
            metadata={"request_id": "req-456", "processing_time": 0.001}
        ),
        LogEntry(
            id="9",
            timestamp=base_time + timedelta(minutes=7),
            level="DEBUG",
            message="Processing request with ID: req-457",
            service_name="request-processor",
            metadata={"request_id": "req-457", "processing_time": 0.002}
        ),
    ]
    
    return logs


async def demonstrate_realtime_streaming():
    """Demonstrate real-time streaming capabilities"""
    
    print("Real-Time Streaming Demo")
    print("=" * 50)
    
    # Create streaming service
    config = StreamConfig(
        buffer_size=100,
        flush_interval=0.5,
        batch_size=5,
        enable_batching=True
    )
    
    service = RealTimeStreamService(config)
    
    # Start the service
    print("Starting real-time streaming service...")
    await service.start()
    
    # Create demo logs
    logs = await create_demo_logs()
    print(f"Created {len(logs)} demo logs")
    
    # Stream logs in real-time
    print("\nStreaming logs in real-time...")
    for i, log in enumerate(logs):
        print(f"  Streaming log {i+1}: [{log.level}] {log.message[:50]}...")
        await service.processor.add_log(log)
        
        # Small delay to simulate real-time streaming
        await asyncio.sleep(0.2)
    
    # Wait for processing
    print("\nWaiting for processing to complete...")
    await asyncio.sleep(2)
    
    # Get metrics
    metrics = service.processor.get_metrics()
    print(f"\nStreaming Metrics:")
    print(f"  Logs Received: {metrics.logs_received}")
    print(f"  Logs Processed: {metrics.logs_processed}")
    print(f"  Logs Filtered: {metrics.logs_filtered}")
    print(f"  Processing Latency: {metrics.processing_latency_ms:.2f}ms")
    print(f"  Throughput: {metrics.throughput_logs_per_second:.1f} logs/second")
    print(f"  Error Count: {metrics.error_count}")
    
    # Get alerts
    alerts = service.processor.get_alerts(10)
    print(f"\nGenerated Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  [{alert.severity.upper()}] {alert.title}")
        print(f"    {alert.message}")
        print(f"    Time: {alert.timestamp}")
        print()
    
    # Stop the service
    await service.stop()
    print("Real-time streaming service stopped")
    
    return service, metrics, alerts


async def demonstrate_visualization():
    """Demonstrate advanced visualization capabilities"""
    
    print("\nAdvanced Visualization Demo")
    print("=" * 50)
    
    # Create dashboard manager
    config = VisualizationConfig(
        refresh_interval=1.0,
        max_data_points=1000,
        enable_animations=True,
        theme="dark"
    )
    
    manager = DashboardManager(config)
    
    # Start the manager
    print("Starting visualization dashboard manager...")
    await manager.start()
    
    # Generate sample visualization data
    print("\nGenerating visualization data...")
    
    # Mock cluster data
    from src.intelligent_analysis import LogCluster
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
        ),
        LogCluster(
            id="cluster_3",
            name="Payment Processing",
            logs=[],
            semantic_summary="Payment transaction events"
        )
    ]
    
    # Generate cluster visualization
    from src.visualization import ClusterVisualizer
    visualizer = ClusterVisualizer()
    cluster_viz = visualizer.visualize_clusters(clusters)
    
    print(f"\nCluster Visualization:")
    for cluster in cluster_viz:
        print(f"  Cluster: {cluster.name}")
        print(f"    Size: {cluster.size} logs")
        print(f"    Color: {cluster.color}")
        print(f"    Position: ({cluster.position['x']:.1f}, {cluster.position['y']:.1f})")
        print(f"    Summary: {cluster.summary}")
        print()
    
    # Mock correlation data
    from src.intelligent_analysis import CorrelationPattern
    correlations = [
        CorrelationPattern(
            id="correlation_1",
            pattern_type="error_sequence",
            events=[],
            correlation_strength=0.85,
            description="Database timeout leading to connection failures"
        ),
        CorrelationPattern(
            id="correlation_2",
            pattern_type="user_flow",
            events=[],
            correlation_strength=0.72,
            description="User login followed by payment processing"
        )
    ]
    
    # Generate correlation timeline
    from src.visualization import CorrelationTimelineVisualizer
    timeline_viz = CorrelationTimelineVisualizer()
    timeline_data = timeline_viz.visualize_correlations(correlations)
    
    print(f"Correlation Timeline:")
    for timeline in timeline_data:
        print(f"  Pattern: {timeline.pattern_type}")
        print(f"    Strength: {timeline.correlation_strength:.2f}")
        print(f"    Description: {timeline.description}")
        print(f"    Events: {len(timeline.events)}")
        print()
    
    # Mock insights data
    from src.intelligent_analysis import LogInsight
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
        ),
        LogInsight(
            id="insight_3",
            title="User Behavior Change",
            type="business",
            severity="medium",
            description="Login pattern changed significantly",
            actionable=True,
            recommended_actions=["Analyze user segments", "Check marketing campaigns"]
        )
    ]
    
    # Generate insights dashboard
    from src.visualization import InsightDashboardGenerator
    insights_generator = InsightDashboardGenerator()
    insights_dashboard = insights_generator.generate_dashboard(insights)
    
    print(f"Insights Dashboard:")
    print(f"  Total Insights: {insights_dashboard.total_insights}")
    print(f"  Critical: {insights_dashboard.critical_insights}")
    print(f"  High: {insights_dashboard.high_insights}")
    print(f"  Medium: {insights_dashboard.medium_insights}")
    print(f"  Low: {insights_dashboard.low_insights}")
    print(f"  Recommendations: {len(insights_dashboard.recommendations)}")
    print()
    
    # Mock metrics data
    from src.realtime_streaming import StreamMetrics
    metrics = StreamMetrics(
        logs_received=1000,
        logs_processed=950,
        logs_filtered=900,
        active_connections=5,
        processing_latency_ms=2.5,
        throughput_logs_per_second=150.0,
        error_count=10
    )
    
    # Generate metrics dashboard
    from src.visualization import MetricsDashboardGenerator
    metrics_generator = MetricsDashboardGenerator()
    metrics_dashboard = metrics_generator.generate_dashboard(metrics)
    
    print(f"Metrics Dashboard:")
    print(f"  Logs/Second: {metrics_dashboard.logs_per_second:.1f}")
    print(f"  Processing Latency: {metrics_dashboard.processing_latency_ms:.2f}ms")
    print(f"  Error Rate: {metrics_dashboard.error_rate:.1%}")
    print(f"  Active Connections: {metrics_dashboard.active_connections}")
    print(f"  Memory Usage: {metrics_dashboard.memory_usage:.1%}")
    print(f"  CPU Usage: {metrics_dashboard.cpu_usage:.1%}")
    print()
    
    # Stop the manager
    await manager.stop()
    print("Visualization dashboard manager stopped")
    
    return {
        "clusters": cluster_viz,
        "correlations": timeline_data,
        "insights": insights_dashboard,
        "metrics": metrics_dashboard
    }


async def demonstrate_integrated_workflow():
    """Demonstrate the complete integrated workflow"""
    
    print("\nIntegrated Workflow Demo")
    print("=" * 50)
    
    # Create logs
    logs = await create_demo_logs()
    print(f"Created {len(logs)} logs for integrated processing")
    
    # Step 1: Intelligent Analysis
    print("\nStep 1: Intelligent Analysis")
    analyzer = IntelligentLogAnalyzer()
    analysis_result = await analyzer.analyze_logs(
        logs=logs,
        analysis_types=["semantic_clustering", "temporal_correlation", "insights"]
    )
    
    print(f"  Generated {len(analysis_result['clusters'])} clusters")
    print(f"  Found {len(analysis_result['correlations'])} correlations")
    print(f"  Created {len(analysis_result['insights'])} insights")
    
    # Step 2: Adaptive Filtering
    print("\nStep 2: Adaptive Filtering")
    filter_engine = AdaptiveLogFilter()
    context = FilterContext(base_sampling_rate=0.1)
    
    decisions = []
    for log in logs:
        decision = await filter_engine.adaptive_filter(log, context)
        decisions.append(decision)
    
    # Analyze filtering results
    error_decisions = [d for d, log in zip(decisions, logs) if log.level == 'ERROR']
    warning_decisions = [d for d, log in zip(decisions, logs) if log.level == 'WARNING']
    info_decisions = [d for d, log in zip(decisions, logs) if log.level == 'INFO']
    
    print(f"  ERROR logs: {len(error_decisions)} logs, avg sampling: {sum(d.sampling_rate for d in error_decisions)/len(error_decisions):.1%}")
    print(f"  WARNING logs: {len(warning_decisions)} logs, avg sampling: {sum(d.sampling_rate for d in warning_decisions)/len(warning_decisions):.1%}")
    print(f"  INFO logs: {len(info_decisions)} logs, avg sampling: {sum(d.sampling_rate for d in info_decisions)/len(info_decisions):.1%}")
    
    # Step 3: Real-Time Streaming
    print("\nStep 3: Real-Time Streaming")
    service = RealTimeStreamService()
    await service.start()
    
    # Stream logs
    for log in logs:
        await service.processor.add_log(log)
    
    await asyncio.sleep(1)  # Wait for processing
    
    metrics = service.processor.get_metrics()
    alerts = service.processor.get_alerts()
    
    print(f"  Streamed {metrics.logs_received} logs")
    print(f"  Processed {metrics.logs_processed} logs")
    print(f"  Generated {len(alerts)} alerts")
    print(f"  Throughput: {metrics.throughput_logs_per_second:.1f} logs/second")
    
    await service.stop()
    
    # Step 4: Visualization
    print("\nStep 4: Advanced Visualization")
    manager = DashboardManager()
    await manager.start()
    
    # Generate visualizations
    from src.visualization import ClusterVisualizer, InsightDashboardGenerator
    cluster_viz = ClusterVisualizer().visualize_clusters(analysis_result['clusters'])
    insights_viz = InsightDashboardGenerator().generate_dashboard(analysis_result['insights'])
    
    print(f"  Generated {len(cluster_viz)} cluster visualizations")
    print(f"  Created insights dashboard with {insights_viz.total_insights} insights")
    print(f"  Provided {len(insights_viz.recommendations)} recommendations")
    
    await manager.stop()
    
    # Summary
    print(f"\nIntegrated Workflow Summary:")
    print(f"  ✅ Intelligent Analysis: {len(analysis_result['insights'])} insights generated")
    print(f"  ✅ Adaptive Filtering: Smart sampling applied to all logs")
    print(f"  ✅ Real-Time Streaming: {metrics.throughput_logs_per_second:.1f} logs/second processed")
    print(f"  ✅ Advanced Visualization: Interactive dashboards created")
    print(f"  ✅ Complete Integration: All systems working together seamlessly")


async def main():
    """Main demonstration function"""
    
    print("LipService: Real-Time Streaming & Advanced Visualization")
    print("=" * 70)
    print("This demo showcases the complete LipService platform with:")
    print("- Real-time log streaming and processing")
    print("- Advanced visualization dashboards")
    print("- Intelligent analysis and adaptive filtering")
    print("- Integrated workflow capabilities")
    print()
    
    try:
        # Demo 1: Real-Time Streaming
        service, metrics, alerts = await demonstrate_realtime_streaming()
        
        # Demo 2: Advanced Visualization
        viz_data = await demonstrate_visualization()
        
        # Demo 3: Integrated Workflow
        await demonstrate_integrated_workflow()
        
        # Final Summary
        print(f"\nComplete Platform Summary")
        print("=" * 70)
        print(f"Real-Time Streaming:")
        print(f"  - Processed {metrics.logs_received} logs")
        print(f"  - Achieved {metrics.throughput_logs_per_second:.1f} logs/second throughput")
        print(f"  - Generated {len(alerts)} real-time alerts")
        print(f"  - Processing latency: {metrics.processing_latency_ms:.2f}ms")
        print()
        print(f"Advanced Visualization:")
        print(f"  - Interactive cluster visualizations")
        print(f"  - Temporal correlation timelines")
        print(f"  - Real-time insights dashboards")
        print(f"  - Live metrics monitoring")
        print()
        print(f"Key Benefits:")
        print(f"  - Real-time processing and analysis")
        print(f"  - Interactive visual dashboards")
        print(f"  - Intelligent adaptive filtering")
        print(f"  - Proactive alerting and monitoring")
        print(f"  - Complete observability platform")
        print()
        print(f"Demo completed successfully!")
        print(f"LipService is now a complete real-time intelligent log management platform")
        print(f"with streaming, visualization, and advanced analytics capabilities.")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
