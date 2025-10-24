"""
Tests for Intelligent Log Analysis and Adaptive Filtering
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.intelligent_analysis import (
    LogEntry, EnrichedLogEntry, LogCluster, CorrelationPattern, LogInsight,
    SemanticLogClusterer, LogMetadataExtractor, TemporalCorrelationEngine,
    LogInsightGenerator, IntelligentLogAnalyzer, SemanticLogSearch
)
from src.adaptive_filtering import (
    FilterContext, SamplingDecision, EnvironmentState, BusinessImpact,
    UserPatterns, CostBenefit, AdaptiveLogFilter, ContextAwareSampler,
    DynamicPatternLearner, PatternMemory
)


class TestSemanticLogClusterer:
    """Test semantic log clustering functionality"""
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample logs for testing"""
        return [
            LogEntry(
                id="1",
                timestamp=datetime.utcnow(),
                level="ERROR",
                message="Database connection failed",
                service_name="user-service"
            ),
            LogEntry(
                id="2", 
                timestamp=datetime.utcnow(),
                level="ERROR",
                message="Database timeout occurred",
                service_name="user-service"
            ),
            LogEntry(
                id="3",
                timestamp=datetime.utcnow(),
                level="INFO",
                message="User login successful",
                service_name="auth-service"
            ),
            LogEntry(
                id="4",
                timestamp=datetime.utcnow(),
                level="INFO", 
                message="User logout completed",
                service_name="auth-service"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_cluster_logs(self, sample_logs):
        """Test basic log clustering"""
        clusterer = SemanticLogClusterer()
        
        clusters = await clusterer.cluster_logs(sample_logs)
        
        assert len(clusters) > 0
        assert all(isinstance(cluster, LogCluster) for cluster in clusters)
        
        # Check that logs are properly assigned to clusters
        total_logs_in_clusters = sum(len(cluster.logs) for cluster in clusters)
        assert total_logs_in_clusters == len(sample_logs)
    
    @pytest.mark.asyncio
    async def test_extract_semantic_content(self, sample_logs):
        """Test semantic content extraction"""
        clusterer = SemanticLogClusterer()
        
        for log in sample_logs:
            content = clusterer._extract_semantic_content(log)
            assert isinstance(content, str)
            assert log.level in content
            assert log.message in content
    
    @pytest.mark.asyncio
    async def test_generate_cluster_summary(self, sample_logs):
        """Test cluster summary generation"""
        clusterer = SemanticLogClusterer()
        
        # Create a test cluster
        cluster = LogCluster(logs=sample_logs[:2])
        
        summary = await clusterer._generate_cluster_summary(cluster)
        
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestLogMetadataExtractor:
    """Test log metadata extraction functionality"""
    
    @pytest.fixture
    def sample_log(self):
        """Create a sample log for testing"""
        return LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="User 12345 failed to authenticate",
            service_name="auth-service"
        )
    
    @pytest.mark.asyncio
    async def test_enrich_log(self, sample_log):
        """Test log enrichment"""
        extractor = LogMetadataExtractor()
        
        enriched_log = await extractor.enrich_log(sample_log)
        
        assert isinstance(enriched_log, EnrichedLogEntry)
        assert enriched_log.original_log == sample_log
        assert isinstance(enriched_log.entities, list)
        assert isinstance(enriched_log.intelligent_tags, list)
        assert 0.0 <= enriched_log.importance_score <= 1.0
        assert isinstance(enriched_log.semantic_content, str)
    
    @pytest.mark.asyncio
    async def test_extract_entities(self, sample_log):
        """Test entity extraction"""
        extractor = LogMetadataExtractor()
        
        entities = await extractor._extract_entities(sample_log)
        
        assert isinstance(entities, list)
        # Should extract user ID from the message
        user_entities = [e for e in entities if e.type == "user_id"]
        assert len(user_entities) > 0
    
    def test_parse_entities(self):
        """Test entity parsing"""
        extractor = LogMetadataExtractor()
        
        # Mock LLM response
        response = "user_ids: [12345], error_types: [authentication]"
        
        # Create a test log
        log = LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="User 12345 failed to authenticate",
            service_name="auth-service"
        )
        
        entities = extractor._parse_entities(response, log)
        
        assert isinstance(entities, list)
        assert len(entities) > 0


class TestTemporalCorrelationEngine:
    """Test temporal correlation analysis"""
    
    @pytest.fixture
    def sample_enriched_logs(self):
        """Create sample enriched logs for testing"""
        base_time = datetime.utcnow()
        
        logs = []
        for i in range(5):
            log = LogEntry(
                id=str(i),
                timestamp=base_time + timedelta(minutes=i),
                level="ERROR" if i % 2 == 0 else "INFO",
                message=f"Event {i} occurred",
                service_name="test-service"
            )
            
            enriched_log = EnrichedLogEntry(
                original_log=log,
                entities=[],
                intelligent_tags=[],
                importance_score=0.5,
                semantic_content=f"ERROR: Event {i} occurred"
            )
            logs.append(enriched_log)
        
        return logs
    
    @pytest.mark.asyncio
    async def test_analyze_temporal_correlations(self, sample_enriched_logs):
        """Test temporal correlation analysis"""
        engine = TemporalCorrelationEngine()
        
        correlations = await engine.analyze_temporal_correlations(sample_enriched_logs)
        
        assert isinstance(correlations, list)
        assert all(isinstance(corr, CorrelationPattern) for corr in correlations)
    
    def test_find_event_sequences(self, sample_enriched_logs):
        """Test event sequence detection"""
        engine = TemporalCorrelationEngine()
        
        sequences = engine._find_event_sequences(sample_enriched_logs)
        
        assert isinstance(sequences, list)
        assert all(isinstance(seq, CorrelationPattern) for seq in sequences)
    
    def test_calculate_correlation_strength(self, sample_enriched_logs):
        """Test correlation strength calculation"""
        engine = TemporalCorrelationEngine()
        
        strength = engine._calculate_correlation_strength(sample_enriched_logs)
        
        assert isinstance(strength, float)
        assert 0.0 <= strength <= 1.0


class TestLogInsightGenerator:
    """Test log insight generation"""
    
    @pytest.fixture
    def sample_enriched_logs(self):
        """Create sample enriched logs for testing"""
        logs = []
        for i in range(10):
            log = LogEntry(
                id=str(i),
                timestamp=datetime.utcnow(),
                level="ERROR" if i < 3 else "INFO",
                message=f"Test message {i}",
                service_name="test-service"
            )
            
            enriched_log = EnrichedLogEntry(
                original_log=log,
                entities=[],
                intelligent_tags=[],
                importance_score=0.5,
                semantic_content=f"ERROR: Test message {i}"
            )
            logs.append(enriched_log)
        
        return logs
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, sample_enriched_logs):
        """Test insight generation"""
        generator = LogInsightGenerator()
        
        insights = await generator.generate_insights(sample_enriched_logs)
        
        assert isinstance(insights, list)
        assert all(isinstance(insight, LogInsight) for insight in insights)
    
    @pytest.mark.asyncio
    async def test_generate_anomaly_insights(self, sample_enriched_logs):
        """Test anomaly insight generation"""
        generator = LogInsightGenerator()
        
        insights = await generator._generate_anomaly_insights(sample_enriched_logs)
        
        assert isinstance(insights, list)
        # Should detect high error rate
        assert len(insights) > 0
    
    @pytest.mark.asyncio
    async def test_generate_performance_insights(self, sample_enriched_logs):
        """Test performance insight generation"""
        generator = LogInsightGenerator()
        
        insights = await generator._generate_performance_insights(sample_enriched_logs)
        
        assert isinstance(insights, list)


class TestIntelligentLogAnalyzer:
    """Test the main intelligent log analyzer"""
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample logs for testing"""
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
    async def test_analyze_logs(self, sample_logs):
        """Test comprehensive log analysis"""
        analyzer = IntelligentLogAnalyzer()
        
        result = await analyzer.analyze_logs(
            logs=sample_logs,
            analysis_types=["semantic_clustering", "temporal_correlation", "insights"]
        )
        
        assert isinstance(result, dict)
        assert 'clusters' in result
        assert 'correlations' in result
        assert 'insights' in result
        assert 'processing_time' in result
        assert 'metadata' in result
        
        assert isinstance(result['clusters'], list)
        assert isinstance(result['correlations'], list)
        assert isinstance(result['insights'], list)
        assert isinstance(result['processing_time'], float)
        assert result['processing_time'] > 0


class TestAdaptiveLogFilter:
    """Test adaptive log filtering functionality"""
    
    @pytest.fixture
    def sample_log(self):
        """Create a sample log for testing"""
        return LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="Database connection failed",
            service_name="user-service"
        )
    
    @pytest.fixture
    def filter_context(self):
        """Create filter context for testing"""
        return FilterContext(
            base_sampling_rate=0.1,
            service_name="test-service",
            user_impact_threshold=1000,
            cost_threshold=100.0
        )
    
    @pytest.mark.asyncio
    async def test_adaptive_filter(self, sample_log, filter_context):
        """Test adaptive filtering"""
        filter_engine = AdaptiveLogFilter()
        
        decision = await filter_engine.adaptive_filter(sample_log, filter_context)
        
        assert isinstance(decision, SamplingDecision)
        assert 0.0 <= decision.sampling_rate <= 1.0
        assert isinstance(decision.reason, str)
        assert 0.0 <= decision.confidence <= 1.0
    
    def test_is_critical_event(self, sample_log):
        """Test critical event detection"""
        filter_engine = AdaptiveLogFilter()
        
        # Create environment state
        env_state = EnvironmentState()
        env_state.high_error_rate = True
        
        is_critical = filter_engine._is_critical_event(sample_log, env_state)
        
        assert isinstance(is_critical, bool)
        # ERROR level should be critical
        assert is_critical is True
    
    @pytest.mark.asyncio
    async def test_calculate_adaptive_rate(self, sample_log, filter_context):
        """Test adaptive rate calculation"""
        filter_engine = AdaptiveLogFilter()
        
        env_state = EnvironmentState()
        env_state.incident_active = True
        
        rate = await filter_engine._calculate_adaptive_rate(sample_log, env_state, filter_context)
        
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 1.0
        # Should be lower during incidents (keep more logs)
        assert rate <= filter_context.base_sampling_rate


class TestContextAwareSampler:
    """Test context-aware sampling functionality"""
    
    @pytest.fixture
    def sample_log(self):
        """Create a sample log for testing"""
        return LogEntry(
            id="1",
            timestamp=datetime.utcnow(),
            level="ERROR",
            message="Payment processing failed for user 12345",
            service_name="payment-service"
        )
    
    @pytest.mark.asyncio
    async def test_context_aware_sample(self, sample_log):
        """Test context-aware sampling"""
        sampler = ContextAwareSampler()
        
        decision = await sampler.context_aware_sample(sample_log)
        
        assert isinstance(decision, SamplingDecision)
        assert 0.0 <= decision.sampling_rate <= 1.0
        assert isinstance(decision.reason, str)
        assert 0.0 <= decision.confidence <= 1.0


class TestDynamicPatternLearner:
    """Test dynamic pattern learning functionality"""
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample logs for testing"""
        return [
            LogEntry(
                id=str(i),
                timestamp=datetime.utcnow(),
                level="ERROR",
                message=f"Database error {i} occurred",
                service_name="db-service"
            )
            for i in range(5)
        ]
    
    @pytest.mark.asyncio
    async def test_learn_and_adapt(self, sample_logs):
        """Test pattern learning and adaptation"""
        learner = DynamicPatternLearner()
        
        result = await learner.learn_and_adapt(sample_logs)
        
        assert isinstance(result, AdaptationResult)
        assert isinstance(result.new_patterns, list)
        assert isinstance(result.adaptations, list)
        assert 0.0 <= result.confidence_score <= 1.0
    
    def test_extract_pattern_key(self, sample_logs):
        """Test pattern key extraction"""
        learner = DynamicPatternLearner()
        
        for log in sample_logs:
            pattern_key = learner._extract_pattern_key(log)
            
            assert isinstance(pattern_key, str)
            assert len(pattern_key) > 0
            assert log.level in pattern_key


class TestPatternMemory:
    """Test pattern memory functionality"""
    
    def test_add_and_get_pattern(self):
        """Test adding and retrieving patterns"""
        memory = PatternMemory()
        
        pattern = LogPattern(
            pattern_id="test_pattern",
            pattern_type="error_pattern",
            frequency=5,
            last_seen=datetime.utcnow(),
            confidence=0.8
        )
        
        memory.add_pattern(pattern)
        
        assert memory.has_pattern("test_pattern")
        retrieved_pattern = memory.get_pattern("test_pattern")
        assert retrieved_pattern == pattern
    
    def test_pattern_eviction(self):
        """Test pattern eviction when limit is exceeded"""
        memory = PatternMemory()
        memory.max_patterns = 5  # Set small limit for testing
        
        # Add more patterns than the limit
        for i in range(10):
            pattern = LogPattern(
                pattern_id=f"pattern_{i}",
                pattern_type="test_pattern",
                frequency=1,
                last_seen=datetime.utcnow(),
                confidence=0.5
            )
            memory.add_pattern(pattern)
        
        # Should have evicted some patterns
        assert len(memory.patterns) <= memory.max_patterns


class TestSemanticLogSearch:
    """Test semantic log search functionality"""
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample logs for testing"""
        return [
            LogEntry(
                id="1",
                timestamp=datetime.utcnow(),
                level="ERROR",
                message="Database connection failed",
                service_name="user-service"
            ),
            LogEntry(
                id="2",
                timestamp=datetime.utcnow(),
                level="INFO",
                message="User login successful",
                service_name="auth-service"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_search(self, sample_logs):
        """Test semantic search functionality"""
        searcher = SemanticLogSearch()
        
        results = await searcher.search("database error", sample_logs, limit=5)
        
        assert isinstance(results, list)
        assert len(results) <= 5
        
        for result in results:
            assert 'log' in result
            assert 'similarity' in result
            assert 'relevance_score' in result
            assert isinstance(result['similarity'], float)
            assert isinstance(result['relevance_score'], float)


class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def comprehensive_logs(self):
        """Create comprehensive logs for integration testing"""
        base_time = datetime.utcnow()
        
        logs = []
        # Error logs
        for i in range(3):
            logs.append(LogEntry(
                id=f"error_{i}",
                timestamp=base_time + timedelta(minutes=i),
                level="ERROR",
                message=f"Database connection failed for user {i}",
                service_name="user-service"
            ))
        
        # Info logs
        for i in range(5):
            logs.append(LogEntry(
                id=f"info_{i}",
                timestamp=base_time + timedelta(minutes=i+3),
                level="INFO",
                message=f"User {i} logged in successfully",
                service_name="auth-service"
            ))
        
        # Warning logs
        for i in range(2):
            logs.append(LogEntry(
                id=f"warning_{i}",
                timestamp=base_time + timedelta(minutes=i+8),
                level="WARNING",
                message=f"High memory usage detected: {80+i}%",
                service_name="monitoring-service"
            ))
        
        return logs
    
    @pytest.mark.asyncio
    async def test_complete_analysis_pipeline(self, comprehensive_logs):
        """Test the complete analysis pipeline"""
        analyzer = IntelligentLogAnalyzer()
        
        # Perform comprehensive analysis
        result = await analyzer.analyze_logs(
            logs=comprehensive_logs,
            analysis_types=["semantic_clustering", "temporal_correlation", "insights"]
        )
        
        # Verify results
        assert len(result['clusters']) > 0
        assert len(result['correlations']) >= 0
        assert len(result['insights']) > 0
        
        # Check that insights are meaningful
        error_insights = [i for i in result['insights'] if i.type == 'anomaly']
        assert len(error_insights) > 0  # Should detect high error rate
    
    @pytest.mark.asyncio
    async def test_adaptive_filtering_integration(self, comprehensive_logs):
        """Test adaptive filtering integration"""
        filter_engine = AdaptiveLogFilter()
        context = FilterContext(base_sampling_rate=0.1)
        
        decisions = []
        for log in comprehensive_logs:
            decision = await filter_engine.adaptive_filter(log, context)
            decisions.append(decision)
        
        assert len(decisions) == len(comprehensive_logs)
        
        # Error logs should have higher sampling rates
        error_decisions = [d for d, log in zip(decisions, comprehensive_logs) if log.level == 'ERROR']
        info_decisions = [d for d, log in zip(decisions, comprehensive_logs) if log.level == 'INFO']
        
        avg_error_rate = sum(d.sampling_rate for d in error_decisions) / len(error_decisions)
        avg_info_rate = sum(d.sampling_rate for d in info_decisions) / len(info_decisions)
        
        # Error logs should be kept more frequently
        assert avg_error_rate < avg_info_rate
    
    @pytest.mark.asyncio
    async def test_pattern_learning_integration(self, comprehensive_logs):
        """Test pattern learning integration"""
        learner = DynamicPatternLearner()
        
        result = await learner.learn_and_adapt(comprehensive_logs)
        
        assert len(result.new_patterns) > 0
        assert len(result.adaptations) >= 0
        assert result.confidence_score > 0
