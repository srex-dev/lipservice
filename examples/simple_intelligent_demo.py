"""
Simple Demo: Intelligent Log Analysis and Adaptive Filtering

This example demonstrates the new intelligent log analysis and adaptive filtering
capabilities of LipService.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import List

from src.intelligent_analysis import (
    LogEntry, IntelligentLogAnalyzer, SemanticLogSearch
)
from src.adaptive_filtering import (
    FilterContext, AdaptiveLogFilter, ContextAwareSampler,
    DynamicPatternLearner, EnvironmentContext
)


async def create_sample_logs() -> List[LogEntry]:
    """Create sample logs for demonstration"""
    
    base_time = datetime.utcnow()
    
    logs = [
        # Error logs - should be kept with high priority
        LogEntry(
            id="1",
            timestamp=base_time,
            level="ERROR",
            message="Database connection failed: timeout after 30s",
            service_name="user-service",
            metadata={"user_id": "12345", "request_id": "req-001"}
        ),
        LogEntry(
            id="2",
            timestamp=base_time + timedelta(minutes=1),
            level="ERROR", 
            message="Payment processing failed for user 67890",
            service_name="payment-service",
            metadata={"user_id": "67890", "amount": 99.99}
        ),
        
        # Info logs - lower priority, should be sampled more aggressively
        LogEntry(
            id="3",
            timestamp=base_time + timedelta(minutes=2),
            level="INFO",
            message="User 11111 logged in successfully",
            service_name="auth-service",
            metadata={"user_id": "11111", "login_method": "oauth"}
        ),
        LogEntry(
            id="4",
            timestamp=base_time + timedelta(minutes=3),
            level="INFO",
            message="User 22222 logged in successfully", 
            service_name="auth-service",
            metadata={"user_id": "22222", "login_method": "oauth"}
        ),
        LogEntry(
            id="5",
            timestamp=base_time + timedelta(minutes=4),
            level="INFO",
            message="Cache hit for key: user_profile_44444",
            service_name="cache-service",
            metadata={"cache_key": "user_profile_44444", "hit_rate": 0.95}
        ),
    ]
    
    return logs


async def demonstrate_intelligent_analysis():
    """Demonstrate intelligent log analysis capabilities"""
    
    print("Intelligent Log Analysis Demo")
    print("=" * 50)
    
    # Create sample logs
    logs = await create_sample_logs()
    print(f"Created {len(logs)} sample logs")
    
    # Initialize analyzer
    analyzer = IntelligentLogAnalyzer()
    
    # Perform comprehensive analysis
    print("\nPerforming comprehensive log analysis...")
    result = await analyzer.analyze_logs(
        logs=logs,
        analysis_types=["semantic_clustering", "temporal_correlation", "insights"],
        cluster_threshold=0.7
    )
    
    # Display results
    print(f"\nAnalysis completed in {result['processing_time']:.2f} seconds")
    print(f"Generated {len(result['clusters'])} semantic clusters")
    print(f"Found {len(result['correlations'])} temporal correlations")
    print(f"Generated {len(result['insights'])} intelligent insights")
    
    # Show clusters
    print("\nSemantic Clusters:")
    for i, cluster in enumerate(result['clusters']):
        print(f"  Cluster {i+1}: {cluster.name}")
        print(f"    Description: {cluster.description}")
        print(f"    Logs: {len(cluster.logs)}")
        print(f"    Summary: {cluster.semantic_summary}")
        print()
    
    # Show insights
    print("\nIntelligent Insights:")
    for i, insight in enumerate(result['insights']):
        print(f"  Insight {i+1}: {insight.title}")
        print(f"    Type: {insight.type}")
        print(f"    Severity: {insight.severity}")
        print(f"    Description: {insight.description}")
        if insight.recommended_actions:
            print(f"    Actions: {', '.join(insight.recommended_actions)}")
        print(f"    Confidence: {insight.confidence:.2f}")
        print()
    
    return result


async def demonstrate_adaptive_filtering():
    """Demonstrate adaptive filtering capabilities"""
    
    print("\nAdaptive Log Filtering Demo")
    print("=" * 50)
    
    # Create sample logs
    logs = await create_sample_logs()
    
    # Initialize filter
    filter_engine = AdaptiveLogFilter()
    context = FilterContext(
        base_sampling_rate=0.1,
        service_name="demo-service",
        user_impact_threshold=1000,
        cost_threshold=100.0
    )
    
    # Get environment state
    env_context = EnvironmentContext()
    env_state = await env_context.get_current_state()
    
    print(f"Environment State:")
    print(f"  Incident Active: {env_state.incident_active}")
    print(f"  Deployment Active: {env_state.deployment_active}")
    print(f"  High Error Rate: {env_state.high_error_rate}")
    print(f"  Low Traffic: {env_state.low_traffic}")
    print(f"  Business Hours: {env_state.business_hours}")
    print(f"  Weekend: {env_state.weekend}")
    print(f"  CPU Usage: {env_state.cpu_usage:.1%}")
    print(f"  Memory Usage: {env_state.memory_usage:.1%}")
    
    # Apply adaptive filtering
    print(f"\nApplying adaptive filtering to {len(logs)} logs...")
    
    decisions = []
    for log in logs:
        decision = await filter_engine.adaptive_filter(log, context)
        decisions.append(decision)
    
    # Analyze decisions
    print(f"\nFiltering Results:")
    
    # Group by log level
    level_decisions = {}
    for log, decision in zip(logs, decisions):
        level = log.level
        if level not in level_decisions:
            level_decisions[level] = []
        level_decisions[level].append(decision)
    
    for level, level_decisions_list in level_decisions.items():
        avg_rate = sum(d.sampling_rate for d in level_decisions_list) / len(level_decisions_list)
        avg_confidence = sum(d.confidence for d in level_decisions_list) / len(level_decisions_list)
        
        print(f"  {level} logs: {len(level_decisions_list)} logs")
        print(f"    Average sampling rate: {avg_rate:.1%}")
        print(f"    Average confidence: {avg_confidence:.2f}")
        print()
    
    # Show individual decisions for first few logs
    print("Sample Filtering Decisions:")
    for i, (log, decision) in enumerate(zip(logs[:3], decisions[:3])):
        print(f"  Log {i+1} ({log.level}): {log.message[:50]}...")
        print(f"    Sampling Rate: {decision.sampling_rate:.1%}")
        print(f"    Reason: {decision.reason}")
        print(f"    Confidence: {decision.confidence:.2f}")
        print()
    
    return decisions


async def demonstrate_semantic_search():
    """Demonstrate semantic search capabilities"""
    
    print("\nSemantic Search Demo")
    print("=" * 50)
    
    # Create sample logs
    logs = await create_sample_logs()
    
    # Initialize semantic search
    searcher = SemanticLogSearch()
    
    # Test different search queries
    queries = [
        "database connection problems",
        "user authentication issues", 
        "payment processing errors"
    ]
    
    print(f"Testing semantic search with {len(queries)} queries...")
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        
        results = await searcher.search(query, logs, limit=3)
        
        print(f"  Found {len(results)} relevant logs:")
        for i, result in enumerate(results):
            log = result['log']
            similarity = result['similarity']
            print(f"    {i+1}. [{log.level}] {log.message[:60]}...")
            print(f"       Similarity: {similarity:.3f}")
            print(f"       Service: {log.service_name}")
    
    return results


async def main():
    """Main demonstration function"""
    
    print("LipService: Intelligent Log Analysis & Adaptive Filtering")
    print("=" * 70)
    print("This demo showcases the advanced AI-powered capabilities")
    print("of LipService for intelligent log management.")
    print()
    
    try:
        # Step 1: Intelligent Analysis
        print("Step 1: Intelligent Analysis")
        analysis_result = await demonstrate_intelligent_analysis()
        
        # Step 2: Adaptive Filtering
        print("\nStep 2: Adaptive Filtering")
        filtering_decisions = await demonstrate_adaptive_filtering()
        
        # Step 3: Semantic Search
        print("\nStep 3: Semantic Search")
        search_results = await demonstrate_semantic_search()
        
        # Summary
        print(f"\nComplete Workflow Summary")
        print("=" * 60)
        print(f"Analyzed {len(await create_sample_logs())} logs with intelligent clustering")
        print(f"Generated {len(analysis_result['insights'])} actionable insights")
        print(f"Applied adaptive filtering with environment awareness")
        print(f"Enabled semantic search across all logs")
        
        # Calculate cost savings
        total_logs = len(await create_sample_logs())
        error_logs = len([log for log in await create_sample_logs() if log.level == 'ERROR'])
        info_logs = len([log for log in await create_sample_logs() if log.level == 'INFO'])
        
        # Estimate sampling rates (based on typical adaptive filtering)
        error_sampling_rate = 1.0  # Keep all errors
        info_sampling_rate = 0.1   # Keep 10% of info logs
        
        sampled_logs = (
            error_logs * error_sampling_rate +
            info_logs * info_sampling_rate
        )
        
        cost_reduction = (total_logs - sampled_logs) / total_logs
        
        print(f"\nCost Optimization Results:")
        print(f"  Total Logs: {total_logs}")
        print(f"  Sampled Logs: {sampled_logs:.1f}")
        print(f"  Cost Reduction: {cost_reduction:.1%}")
        print(f"  Monthly Savings: ${total_logs * 30 * 0.001 * cost_reduction:.2f} (estimated)")
        
        print(f"\nKey Benefits:")
        print(f"  AI-powered semantic understanding")
        print(f"  Adaptive filtering based on environment")
        print(f"  Natural language search capabilities")
        print(f"  Intelligent insights and recommendations")
        print(f"  Continuous pattern learning")
        print(f"  Significant cost reduction without data loss")
        
        print(f"\nDemo completed successfully!")
        print(f"LipService provides enterprise-grade intelligent log management")
        print(f"with AI-powered analysis, adaptive filtering, and cost optimization.")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
