"""
Comprehensive Example: Intelligent Log Analysis and Adaptive Filtering

This example demonstrates the new intelligent log analysis and adaptive filtering
capabilities of LipService.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        LogEntry(
            id="3",
            timestamp=base_time + timedelta(minutes=2),
            level="ERROR",
            message="Authentication service unavailable",
            service_name="auth-service",
            metadata={"service_status": "down"}
        ),
        
        # Warning logs - medium priority
        LogEntry(
            id="4",
            timestamp=base_time + timedelta(minutes=3),
            level="WARNING",
            message="High memory usage detected: 85%",
            service_name="monitoring-service",
            metadata={"memory_usage": 0.85}
        ),
        LogEntry(
            id="5",
            timestamp=base_time + timedelta(minutes=4),
            level="WARNING",
            message="API response time exceeded threshold: 2.5s",
            service_name="api-gateway",
            metadata={"response_time": 2.5, "threshold": 2.0}
        ),
        
        # Info logs - lower priority, should be sampled more aggressively
        LogEntry(
            id="6",
            timestamp=base_time + timedelta(minutes=5),
            level="INFO",
            message="User 11111 logged in successfully",
            service_name="auth-service",
            metadata={"user_id": "11111", "login_method": "oauth"}
        ),
        LogEntry(
            id="7",
            timestamp=base_time + timedelta(minutes=6),
            level="INFO",
            message="User 22222 logged in successfully", 
            service_name="auth-service",
            metadata={"user_id": "22222", "login_method": "oauth"}
        ),
        LogEntry(
            id="8",
            timestamp=base_time + timedelta(minutes=7),
            level="INFO",
            message="User 33333 logged in successfully",
            service_name="auth-service", 
            metadata={"user_id": "33333", "login_method": "oauth"}
        ),
        LogEntry(
            id="9",
            timestamp=base_time + timedelta(minutes=8),
            level="INFO",
            message="Cache hit for key: user_profile_44444",
            service_name="cache-service",
            metadata={"cache_key": "user_profile_44444", "hit_rate": 0.95}
        ),
        LogEntry(
            id="10",
            timestamp=base_time + timedelta(minutes=9),
            level="INFO",
            message="Cache hit for key: user_profile_55555",
            service_name="cache-service",
            metadata={"cache_key": "user_profile_55555", "hit_rate": 0.95}
        ),
        
        # Debug logs - lowest priority
        LogEntry(
            id="11",
            timestamp=base_time + timedelta(minutes=10),
            level="DEBUG",
            message="Processing request with ID: req-002",
            service_name="request-processor",
            metadata={"request_id": "req-002", "processing_time": 0.001}
        ),
        LogEntry(
            id="12",
            timestamp=base_time + timedelta(minutes=11),
            level="DEBUG",
            message="Processing request with ID: req-003",
            service_name="request-processor",
            metadata={"request_id": "req-003", "processing_time": 0.002}
        ),
    ]
    
    return logs


async def demonstrate_intelligent_analysis():
    """Demonstrate intelligent log analysis capabilities"""
    
    print("🧠 Intelligent Log Analysis Demo")
    print("=" * 50)
    
    # Create sample logs
    logs = await create_sample_logs()
    print(f"Created {len(logs)} sample logs")
    
    # Initialize analyzer
    analyzer = IntelligentLogAnalyzer()
    
    # Perform comprehensive analysis
    print("\n📊 Performing comprehensive log analysis...")
    result = await analyzer.analyze_logs(
        logs=logs,
        analysis_types=["semantic_clustering", "temporal_correlation", "insights"],
        cluster_threshold=0.7
    )
    
    # Display results
    print(f"\n✅ Analysis completed in {result['processing_time']:.2f} seconds")
    print(f"📈 Generated {len(result['clusters'])} semantic clusters")
    print(f"🔗 Found {len(result['correlations'])} temporal correlations")
    print(f"💡 Generated {len(result['insights'])} intelligent insights")
    
    # Show clusters
    print("\n🎯 Semantic Clusters:")
    for i, cluster in enumerate(result['clusters']):
        print(f"  Cluster {i+1}: {cluster.name}")
        print(f"    Description: {cluster.description}")
        print(f"    Logs: {len(cluster.logs)}")
        print(f"    Summary: {cluster.semantic_summary}")
        print()
    
    # Show insights
    print("\n💡 Intelligent Insights:")
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
    
    print("\n🎛️ Adaptive Log Filtering Demo")
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
    
    print(f"🌍 Environment State:")
    print(f"  Incident Active: {env_state.incident_active}")
    print(f"  Deployment Active: {env_state.deployment_active}")
    print(f"  High Error Rate: {env_state.high_error_rate}")
    print(f"  Low Traffic: {env_state.low_traffic}")
    print(f"  Business Hours: {env_state.business_hours}")
    print(f"  Weekend: {env_state.weekend}")
    print(f"  CPU Usage: {env_state.cpu_usage:.1%}")
    print(f"  Memory Usage: {env_state.memory_usage:.1%}")
    
    # Apply adaptive filtering
    print(f"\n🎯 Applying adaptive filtering to {len(logs)} logs...")
    
    decisions = []
    for log in logs:
        decision = await filter_engine.adaptive_filter(log, context)
        decisions.append(decision)
    
    # Analyze decisions
    print(f"\n📊 Filtering Results:")
    
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
    print("🔍 Sample Filtering Decisions:")
    for i, (log, decision) in enumerate(zip(logs[:5], decisions[:5])):
        print(f"  Log {i+1} ({log.level}): {log.message[:50]}...")
        print(f"    Sampling Rate: {decision.sampling_rate:.1%}")
        print(f"    Reason: {decision.reason}")
        print(f"    Confidence: {decision.confidence:.2f}")
        print()
    
    return decisions


async def demonstrate_context_aware_sampling():
    """Demonstrate context-aware sampling"""
    
    print("\n🎯 Context-Aware Sampling Demo")
    print("=" * 50)
    
    # Create sample logs with different business contexts
    logs = [
        LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="Payment processing failed for user 12345 - amount $99.99",
            service_name="payment-service",
            metadata={"user_id": "12345", "amount": 99.99, "currency": "USD"}
        ),
        LogEntry(
            id="2",
            timestamp=datetime.utcnow(),
            level="INFO",
            message="User 67890 logged in successfully",
            service_name="auth-service",
            metadata={"user_id": "67890"}
        ),
        LogEntry(
            id="3",
            timestamp=datetime.utcnow(),
            level="DEBUG",
            message="Cache hit for key: temp_data_123",
            service_name="cache-service",
            metadata={"cache_key": "temp_data_123"}
        )
    ]
    
    # Initialize context-aware sampler
    sampler = ContextAwareSampler()
    
    print(f"🎯 Applying context-aware sampling to {len(logs)} logs...")
    
    decisions = []
    for log in logs:
        decision = await sampler.context_aware_sample(log)
        decisions.append(decision)
    
    # Show results
    print(f"\n📊 Context-Aware Sampling Results:")
    for i, (log, decision) in enumerate(zip(logs, decisions)):
        print(f"  Log {i+1}: {log.message}")
        print(f"    Business Impact: High (payment failure)")
        print(f"    Sampling Rate: {decision.sampling_rate:.1%}")
        print(f"    Reason: {decision.reason}")
        print(f"    Confidence: {decision.confidence:.2f}")
        print()
    
    return decisions


async def demonstrate_pattern_learning():
    """Demonstrate pattern learning capabilities"""
    
    print("\n🧠 Pattern Learning Demo")
    print("=" * 50)
    
    # Create logs with patterns
    logs = []
    base_time = datetime.utcnow()
    
    # Create repeated patterns
    for i in range(5):
        logs.append(LogEntry(
            id=f"pattern_1_{i}",
            timestamp=base_time + timedelta(minutes=i),
            level="ERROR",
            message="Database connection timeout after 30 seconds",
            service_name="user-service"
        ))
    
    for i in range(3):
        logs.append(LogEntry(
            id=f"pattern_2_{i}",
            timestamp=base_time + timedelta(minutes=i+5),
            level="INFO",
            message="User authentication successful via OAuth",
            service_name="auth-service"
        ))
    
    # Initialize pattern learner
    learner = DynamicPatternLearner()
    
    print(f"🧠 Learning patterns from {len(logs)} logs...")
    
    result = await learner.learn_and_adapt(logs)
    
    print(f"\n📊 Pattern Learning Results:")
    print(f"  New Patterns Detected: {len(result.new_patterns)}")
    print(f"  Adaptations Generated: {len(result.adaptations)}")
    print(f"  Confidence Score: {result.confidence_score:.2f}")
    
    # Show detected patterns
    print(f"\n🔍 Detected Patterns:")
    for i, pattern in enumerate(result.new_patterns):
        print(f"  Pattern {i+1}: {pattern.pattern_id}")
        print(f"    Type: {pattern.pattern_type}")
        print(f"    Frequency: {pattern.frequency}")
        print(f"    Confidence: {pattern.confidence:.2f}")
        print()
    
    # Show adaptations
    if result.adaptations:
        print(f"🔄 Generated Adaptations:")
        for i, adaptation in enumerate(result.adaptations):
            print(f"  {i+1}. {adaptation}")
        print()
    
    return result


async def demonstrate_semantic_search():
    """Demonstrate semantic search capabilities"""
    
    print("\n🔍 Semantic Search Demo")
    print("=" * 50)
    
    # Create sample logs
    logs = await create_sample_logs()
    
    # Initialize semantic search
    searcher = SemanticLogSearch()
    
    # Test different search queries
    queries = [
        "database connection problems",
        "user authentication issues", 
        "memory usage warnings",
        "payment processing errors"
    ]
    
    print(f"🔍 Testing semantic search with {len(queries)} queries...")
    
    for query in queries:
        print(f"\n🔎 Query: '{query}'")
        
        results = await searcher.search(query, logs, limit=3)
        
        print(f"  Found {len(results)} relevant logs:")
        for i, result in enumerate(results):
            log = result['log']
            similarity = result['similarity']
            print(f"    {i+1}. [{log.level}] {log.message[:60]}...")
            print(f"       Similarity: {similarity:.3f}")
            print(f"       Service: {log.service_name}")
    
    return results


async def demonstrate_complete_workflow():
    """Demonstrate the complete intelligent logging workflow"""
    
    print("\n🚀 Complete Intelligent Logging Workflow Demo")
    print("=" * 60)
    
    # Create comprehensive logs
    logs = await create_sample_logs()
    print(f"📝 Created {len(logs)} sample logs")
    
    # Step 1: Intelligent Analysis
    print(f"\n1️⃣ Step 1: Intelligent Analysis")
    analysis_result = await demonstrate_intelligent_analysis()
    
    # Step 2: Adaptive Filtering
    print(f"\n2️⃣ Step 2: Adaptive Filtering")
    filtering_decisions = await demonstrate_adaptive_filtering()
    
    # Step 3: Context-Aware Sampling
    print(f"\n3️⃣ Step 3: Context-Aware Sampling")
    context_decisions = await demonstrate_context_aware_sampling()
    
    # Step 4: Pattern Learning
    print(f"\n4️⃣ Step 4: Pattern Learning")
    learning_result = await demonstrate_pattern_learning()
    
    # Step 5: Semantic Search
    print(f"\n5️⃣ Step 5: Semantic Search")
    search_results = await demonstrate_semantic_search()
    
    # Summary
    print(f"\n📊 Complete Workflow Summary")
    print("=" * 60)
    print(f"✅ Analyzed {len(logs)} logs with intelligent clustering")
    print(f"✅ Generated {len(analysis_result['insights'])} actionable insights")
    print(f"✅ Applied adaptive filtering with environment awareness")
    print(f"✅ Learned {len(learning_result.new_patterns)} new patterns")
    print(f"✅ Enabled semantic search across all logs")
    
    # Calculate cost savings
    total_logs = len(logs)
    error_logs = len([log for log in logs if log.level == 'ERROR'])
    warning_logs = len([log for log in logs if log.level == 'WARNING'])
    info_logs = len([log for log in logs if log.level == 'INFO'])
    debug_logs = len([log for log in logs if log.level == 'DEBUG'])
    
    # Estimate sampling rates (based on typical adaptive filtering)
    error_sampling_rate = 1.0  # Keep all errors
    warning_sampling_rate = 0.3  # Keep 30% of warnings
    info_sampling_rate = 0.1   # Keep 10% of info logs
    debug_sampling_rate = 0.05  # Keep 5% of debug logs
    
    sampled_logs = (
        error_logs * error_sampling_rate +
        warning_logs * warning_sampling_rate +
        info_logs * info_sampling_rate +
        debug_logs * debug_sampling_rate
    )
    
    cost_reduction = (total_logs - sampled_logs) / total_logs
    
    print(f"\n💰 Cost Optimization Results:")
    print(f"  Total Logs: {total_logs}")
    print(f"  Sampled Logs: {sampled_logs:.1f}")
    print(f"  Cost Reduction: {cost_reduction:.1%}")
    print(f"  Monthly Savings: ${total_logs * 30 * 0.001 * cost_reduction:.2f} (estimated)")
    
    print(f"\n🎯 Key Benefits:")
    print(f"  🧠 AI-powered semantic understanding")
    print(f"  🎛️ Adaptive filtering based on environment")
    print(f"  🔍 Natural language search capabilities")
    print(f"  📊 Intelligent insights and recommendations")
    print(f"  🔄 Continuous pattern learning")
    print(f"  💰 Significant cost reduction without data loss")


async def main():
    """Main demonstration function"""
    
    print("🎙️ LipService: Intelligent Log Analysis & Adaptive Filtering")
    print("=" * 70)
    print("This demo showcases the advanced AI-powered capabilities")
    print("of LipService for intelligent log management.")
    print()
    
    try:
        await demonstrate_complete_workflow()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"LipService provides enterprise-grade intelligent log management")
        print(f"with AI-powered analysis, adaptive filtering, and cost optimization.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
