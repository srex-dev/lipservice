"""
Adaptive Log Filtering System

This module provides intelligent, adaptive log filtering that learns from
environment context and dynamically adjusts sampling strategies.
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class LogContext:
    """Simple log context for adaptive filtering"""
    
    def __init__(self, **kwargs):
        self.data = kwargs
    
    def __repr__(self):
        return f"LogContext({self.data})"


class FilterDecision(Enum):
    """Filter decision types"""
    KEEP_ALL = "keep_all"
    KEEP_SOME = "keep_some"
    KEEP_NONE = "keep_none"
    ADAPTIVE_SAMPLE = "adaptive_sample"


class EnvironmentState:
    """Current state of the environment"""
    
    def __init__(self):
        self.incident_active = False
        self.deployment_active = False
        self.high_error_rate = False
        self.low_traffic = False
        self.business_hours = False
        self.weekend = False
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.error_count = 0
        self.total_logs = 0
        self.last_updated = datetime.utcnow()


class FilterContext:
    """Context for filtering decisions"""
    
    def __init__(self, base_sampling_rate: float = 0.1, service_name: str = None,
                 user_impact_threshold: int = 1000, cost_threshold: float = 100.0):
        self.base_sampling_rate = base_sampling_rate
        self.service_name = service_name
        self.user_impact_threshold = user_impact_threshold
        self.cost_threshold = cost_threshold
        self.last_decision_time = datetime.utcnow()


class SamplingDecision:
    """Decision about log sampling"""
    
    def __init__(self, sampling_rate: float, reason: str, confidence: float = 1.0,
                 decision_type: FilterDecision = FilterDecision.ADAPTIVE_SAMPLE):
        self.sampling_rate = sampling_rate
        self.reason = reason
        self.confidence = confidence
        self.decision_type = decision_type
        self.timestamp = datetime.utcnow()


class BusinessImpact:
    """Business impact assessment"""
    
    def __init__(self, level: str = "low", affected_users: int = 0, 
                 revenue_impact: float = 0.0, compliance_risk: bool = False):
        self.level = level  # critical, high, medium, low
        self.affected_users = affected_users
        self.revenue_impact = revenue_impact
        self.compliance_risk = compliance_risk


class UserPatterns:
    """User behavior patterns"""
    
    def __init__(self, affected_users: int = 0, user_segments: List[str] = None,
                 peak_hours: bool = False, geographic_distribution: Dict[str, int] = None):
        self.affected_users = affected_users
        self.user_segments = user_segments or []
        self.peak_hours = peak_hours
        self.geographic_distribution = geographic_distribution or {}


class CostBenefit:
    """Cost-benefit analysis"""
    
    def __init__(self, storage_cost: float = 0.0, processing_cost: float = 0.0,
                 debugging_value: float = 0.0, compliance_value: float = 0.0):
        self.storage_cost = storage_cost
        self.processing_cost = processing_cost
        self.debugging_value = debugging_value
        self.compliance_value = compliance_value
        self.ratio = self._calculate_ratio()
    
    def _calculate_ratio(self) -> float:
        """Calculate cost-benefit ratio"""
        total_cost = self.storage_cost + self.processing_cost
        total_value = self.debugging_value + self.compliance_value
        
        if total_cost == 0:
            return 1.0
        
        return total_value / total_cost


class LogPattern:
    """Learned log pattern"""
    
    def __init__(self, pattern_id: str, pattern_type: str, frequency: int,
                 last_seen: datetime, confidence: float = 1.0):
        self.pattern_id = pattern_id
        self.pattern_type = pattern_type
        self.frequency = frequency
        self.last_seen = last_seen
        self.confidence = confidence


class AdaptationResult:
    """Result of pattern adaptation"""
    
    def __init__(self, new_patterns: List[LogPattern], adaptations: List[str],
                 confidence_score: float):
        self.new_patterns = new_patterns
        self.adaptations = adaptations
        self.confidence_score = confidence_score


class EnvironmentContext:
    """Analyzes current environment state"""
    
    def __init__(self):
        self.state_history = []
        self.metrics_window = timedelta(minutes=5)
    
    async def get_current_state(self) -> EnvironmentState:
        """Get current environment state"""
        state = EnvironmentState()
        
        # Analyze recent metrics
        await self._analyze_metrics(state)
        
        # Check for incidents
        await self._check_incidents(state)
        
        # Check deployment status
        await self._check_deployments(state)
        
        # Check business hours
        self._check_business_hours(state)
        
        return state
    
    async def _analyze_metrics(self, state: EnvironmentState):
        """Analyze system metrics"""
        # Mock metrics analysis (in production, this would query real metrics)
        state.cpu_usage = 0.5  # 50% CPU usage
        state.memory_usage = 0.6  # 60% memory usage
        
        # Determine if traffic is low
        if state.cpu_usage < 0.3 and state.memory_usage < 0.4:
            state.low_traffic = True
    
    async def _check_incidents(self, state: EnvironmentState):
        """Check for active incidents"""
        # Mock incident check (in production, this would query incident management)
        state.incident_active = False  # No active incidents
        state.high_error_rate = False  # Normal error rate
    
    async def _check_deployments(self, state: EnvironmentState):
        """Check for active deployments"""
        # Mock deployment check (in production, this would query deployment systems)
        state.deployment_active = False  # No active deployments
    
    def _check_business_hours(self, state: EnvironmentState):
        """Check if it's business hours"""
        now = datetime.utcnow()
        
        # Business hours: Monday-Friday, 9 AM - 5 PM UTC
        if now.weekday() < 5 and 9 <= now.hour < 17:
            state.business_hours = True
        
        # Weekend check
        if now.weekday() >= 5:
            state.weekend = True


class AdaptiveLogFilter:
    """AI-powered adaptive filtering that learns from environment"""
    
    def __init__(self):
        self.environment_context = EnvironmentContext()
        self.learning_engine = FilterLearningEngine()
        self.decision_history = []
    
    async def adaptive_filter(self, log: 'LogEntry', context: FilterContext) -> SamplingDecision:
        """Dynamically adjust filtering based on environment state"""
        
        # 1. Analyze current environment state
        env_state = await self.environment_context.get_current_state()
        
        # 2. Check for critical events
        if self._is_critical_event(log, env_state):
            return SamplingDecision(
                sampling_rate=1.0,
                reason="Critical event detected",
                confidence=1.0,
                decision_type=FilterDecision.KEEP_ALL
            )
        
        # 3. Apply adaptive sampling based on context
        sampling_rate = await self._calculate_adaptive_rate(log, env_state, context)
        
        # 4. Learn from filtering decisions
        decision = SamplingDecision(
            sampling_rate=sampling_rate,
            reason=self._get_reason(env_state),
            confidence=self._calculate_confidence(env_state),
            decision_type=FilterDecision.ADAPTIVE_SAMPLE
        )
        
        await self.learning_engine.record_decision(log, decision, env_state)
        self.decision_history.append(decision)
        
        return decision
    
    def _is_critical_event(self, log: 'LogEntry', env_state: EnvironmentState) -> bool:
        """Check if this is a critical event that should always be kept"""
        
        # Critical log levels
        if log.level in ['ERROR', 'CRITICAL', 'FATAL']:
            return True
        
        # Critical keywords
        critical_keywords = ['outage', 'down', 'critical', 'emergency', 'security']
        if any(keyword in log.message.lower() for keyword in critical_keywords):
            return True
        
        # High error rate in environment
        if env_state.high_error_rate and log.level == 'ERROR':
            return True
        
        return False
    
    async def _calculate_adaptive_rate(self, log: 'LogEntry', env_state: EnvironmentState, 
                                     context: FilterContext) -> float:
        """Calculate adaptive sampling rate based on multiple factors"""
        
        base_rate = context.base_sampling_rate
        
        # Adjust based on environment factors
        adjustments = {
            'incident_active': 0.1,      # Keep more during incidents
            'deployment_active': 0.05,   # Keep more during deployments
            'high_error_rate': 0.02,     # Keep more when errors spike
            'low_traffic': 0.8,          # Sample more during low traffic
            'business_hours': 0.3,       # Keep more during business hours
            'weekend': 0.7,              # Sample more on weekends
        }
        
        for factor, adjustment in adjustments.items():
            if await self._factor_is_active(factor, env_state):
                base_rate = min(base_rate, adjustment)
        
        # Adjust based on log level
        level_adjustments = {
            'ERROR': 0.1,
            'WARNING': 0.3,
            'INFO': 0.5,
            'DEBUG': 0.8
        }
        
        level_adjustment = level_adjustments.get(log.level, 0.5)
        base_rate = min(base_rate, level_adjustment)
        
        return max(base_rate, 0.01)  # Minimum 1% sampling
    
    async def _factor_is_active(self, factor: str, env_state: EnvironmentState) -> bool:
        """Check if a specific factor is active"""
        factor_map = {
            'incident_active': env_state.incident_active,
            'deployment_active': env_state.deployment_active,
            'high_error_rate': env_state.high_error_rate,
            'low_traffic': env_state.low_traffic,
            'business_hours': env_state.business_hours,
            'weekend': env_state.weekend,
        }
        
        return factor_map.get(factor, False)
    
    def _get_reason(self, env_state: EnvironmentState) -> str:
        """Generate human-readable reason for sampling decision"""
        reasons = []
        
        if env_state.incident_active:
            reasons.append("incident active")
        if env_state.deployment_active:
            reasons.append("deployment active")
        if env_state.high_error_rate:
            reasons.append("high error rate")
        if env_state.low_traffic:
            reasons.append("low traffic")
        if env_state.business_hours:
            reasons.append("business hours")
        if env_state.weekend:
            reasons.append("weekend")
        
        if reasons:
            return f"Adjusted due to: {', '.join(reasons)}"
        else:
            return "Standard adaptive sampling"
    
    def _calculate_confidence(self, env_state: EnvironmentState) -> float:
        """Calculate confidence in the sampling decision"""
        confidence = 0.8  # Base confidence
        
        # Increase confidence if we have clear environmental signals
        if env_state.incident_active or env_state.deployment_active:
            confidence += 0.1
        
        # Decrease confidence if environment is ambiguous
        if not any([env_state.incident_active, env_state.deployment_active, 
                   env_state.high_error_rate, env_state.low_traffic]):
            confidence -= 0.1
        
        return max(min(confidence, 1.0), 0.0)


class FilterLearningEngine:
    """Learns from filtering decisions to improve future decisions"""
    
    def __init__(self):
        self.decision_history = []
        self.pattern_memory = PatternMemory()
        self.performance_tracker = PerformanceTracker()
    
    async def record_decision(self, log: 'LogEntry', decision: SamplingDecision, 
                             env_state: EnvironmentState):
        """Record a filtering decision for learning"""
        
        decision_record = {
            'log': log,
            'decision': decision,
            'env_state': env_state,
            'timestamp': datetime.utcnow()
        }
        
        self.decision_history.append(decision_record)
        
        # Keep only recent history
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.decision_history = [
            record for record in self.decision_history
            if record['timestamp'] > cutoff_time
        ]
    
    async def learn_from_decisions(self) -> List[str]:
        """Learn patterns from decision history"""
        learnings = []
        
        if len(self.decision_history) < 10:
            return learnings
        
        # Analyze decision patterns
        error_decisions = [
            record for record in self.decision_history
            if record['log'].level == 'ERROR'
        ]
        
        if len(error_decisions) > 0:
            avg_error_sampling = sum(
                record['decision'].sampling_rate for record in error_decisions
            ) / len(error_decisions)
            
            if avg_error_sampling < 0.2:
                learnings.append("Consider keeping more error logs for debugging")
        
        return learnings


class PatternMemory:
    """Stores and manages learned patterns"""
    
    def __init__(self):
        self.patterns = {}
        self.max_patterns = 1000
    
    def add_pattern(self, pattern: LogPattern):
        """Add a new pattern to memory"""
        self.patterns[pattern.pattern_id] = pattern
        
        # Evict old patterns if we exceed limit
        if len(self.patterns) > self.max_patterns:
            self._evict_old_patterns()
    
    def has_pattern(self, pattern_id: str) -> bool:
        """Check if pattern exists in memory"""
        return pattern_id in self.patterns
    
    def get_pattern(self, pattern_id: str) -> Optional[LogPattern]:
        """Get pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def _evict_old_patterns(self):
        """Evict least recently used patterns"""
        sorted_patterns = sorted(
            self.patterns.items(),
            key=lambda x: x[1].last_seen
        )
        
        # Remove oldest 10% of patterns
        evict_count = len(sorted_patterns) // 10
        for pattern_id, _ in sorted_patterns[:evict_count]:
            del self.patterns[pattern_id]


class PerformanceTracker:
    """Tracks performance of filtering decisions"""
    
    def __init__(self):
        self.metrics = {
            'total_decisions': 0,
            'correct_decisions': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
    
    def record_decision_outcome(self, decision: SamplingDecision, was_correct: bool):
        """Record the outcome of a filtering decision"""
        self.metrics['total_decisions'] += 1
        
        if was_correct:
            self.metrics['correct_decisions'] += 1
        else:
            if decision.sampling_rate > 0.5:
                self.metrics['false_positives'] += 1
            else:
                self.metrics['false_negatives'] += 1
    
    def get_accuracy(self) -> float:
        """Get current accuracy of filtering decisions"""
        if self.metrics['total_decisions'] == 0:
            return 0.0
        
        return self.metrics['correct_decisions'] / self.metrics['total_decisions']


class DynamicPatternLearner:
    """Continuously learns and adapts to new log patterns"""
    
    def __init__(self):
        self.pattern_memory = PatternMemory()
        self.change_detector = PatternChangeDetector()
        self.adaptation_engine = AdaptationEngine()
    
    async def learn_and_adapt(self, logs: List['LogEntry']) -> AdaptationResult:
        """Learn from new logs and adapt filtering strategies"""
        
        # 1. Detect new patterns
        new_patterns = await self._detect_new_patterns(logs)
        
        # 2. Identify pattern changes
        changes = await self.change_detector.detect_changes(new_patterns)
        
        # 3. Adapt filtering strategies
        adaptations = await self.adaptation_engine.adapt_to_changes(changes)
        
        # 4. Update pattern memory
        for pattern in new_patterns:
            self.pattern_memory.add_pattern(pattern)
        
        return AdaptationResult(
            new_patterns=new_patterns,
            adaptations=adaptations,
            confidence_score=self._calculate_confidence(adaptations)
        )
    
    async def _detect_new_patterns(self, logs: List['LogEntry']) -> List[LogPattern]:
        """Detect previously unseen log patterns"""
        
        patterns = []
        
        # Group logs by message patterns
        message_groups = {}
        for log in logs:
            # Simple pattern extraction (in production, use more sophisticated methods)
            pattern_key = self._extract_pattern_key(log)
            
            if pattern_key not in message_groups:
                message_groups[pattern_key] = []
            message_groups[pattern_key].append(log)
        
        # Create patterns for groups with multiple logs
        for pattern_key, log_group in message_groups.items():
            if len(log_group) > 1 and not self.pattern_memory.has_pattern(pattern_key):
                pattern = LogPattern(
                    pattern_id=pattern_key,
                    pattern_type="message_pattern",
                    frequency=len(log_group),
                    last_seen=datetime.utcnow(),
                    confidence=min(len(log_group) / 10.0, 1.0)
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_pattern_key(self, log: 'LogEntry') -> str:
        """Extract a pattern key from a log entry"""
        # Simple pattern extraction (replace with more sophisticated methods)
        import re
        
        # Remove variable parts (numbers, IDs, etc.)
        pattern = re.sub(r'\d+', 'N', log.message)
        pattern = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', pattern)
        
        return f"{log.level}:{pattern}"
    
    def _calculate_confidence(self, adaptations: List[str]) -> float:
        """Calculate confidence in adaptations"""
        if not adaptations:
            return 0.5
        
        # Higher confidence with more adaptations
        confidence = min(len(adaptations) / 5.0, 1.0)
        return confidence


class PatternChangeDetector:
    """Detects changes in log patterns"""
    
    def __init__(self):
        self.baseline_patterns = {}
        self.change_threshold = 0.3
    
    async def detect_changes(self, new_patterns: List[LogPattern]) -> List[str]:
        """Detect significant changes in patterns"""
        changes = []
        
        for pattern in new_patterns:
            if pattern.pattern_id in self.baseline_patterns:
                baseline = self.baseline_patterns[pattern.pattern_id]
                
                # Check frequency change
                freq_change = abs(pattern.frequency - baseline.frequency) / baseline.frequency
                if freq_change > self.change_threshold:
                    changes.append(f"Frequency change in pattern {pattern.pattern_id}")
                
                # Check confidence change
                conf_change = abs(pattern.confidence - baseline.confidence)
                if conf_change > self.change_threshold:
                    changes.append(f"Confidence change in pattern {pattern.pattern_id}")
            else:
                changes.append(f"New pattern detected: {pattern.pattern_id}")
        
        # Update baseline
        for pattern in new_patterns:
            self.baseline_patterns[pattern.pattern_id] = pattern
        
        return changes


class AdaptationEngine:
    """Adapts filtering strategies based on pattern changes"""
    
    def __init__(self):
        self.adaptation_rules = {
            'frequency_increase': 'Increase sampling for high-frequency patterns',
            'confidence_decrease': 'Reduce sampling for low-confidence patterns',
            'new_pattern': 'Monitor new patterns closely'
        }
    
    async def adapt_to_changes(self, changes: List[str]) -> List[str]:
        """Generate adaptations based on detected changes"""
        adaptations = []
        
        for change in changes:
            if 'frequency change' in change:
                adaptations.append(self.adaptation_rules['frequency_increase'])
            elif 'confidence change' in change:
                adaptations.append(self.adaptation_rules['confidence_decrease'])
            elif 'new pattern' in change:
                adaptations.append(self.adaptation_rules['new_pattern'])
        
        return adaptations


class ContextAwareSampler:
    """Sampling that considers business context and user behavior"""
    
    def __init__(self):
        self.business_context = BusinessContextAnalyzer()
        self.user_behavior = UserBehaviorAnalyzer()
        self.cost_optimizer = CostOptimizer()
    
    async def context_aware_sample(self, log: 'LogEntry') -> SamplingDecision:
        """Sample based on business context and user impact"""
        
        # 1. Analyze business context
        business_impact = await self.business_context.analyze_impact(log)
        
        # 2. Check user behavior patterns
        user_patterns = await self.user_behavior.analyze_patterns(log)
        
        # 3. Calculate cost-benefit
        cost_benefit = await self.cost_optimizer.calculate_cost_benefit(log)
        
        # 4. Make sampling decision
        decision = self._make_sampling_decision(business_impact, user_patterns, cost_benefit)
        
        return decision
    
    def _make_sampling_decision(self, business_impact: BusinessImpact, 
                               user_patterns: UserPatterns, 
                               cost_benefit: CostBenefit) -> SamplingDecision:
        """Make intelligent sampling decision"""
        
        # High business impact = keep more
        if business_impact.level == "critical":
            return SamplingDecision(
                sampling_rate=1.0,
                reason="Critical business impact",
                confidence=1.0,
                decision_type=FilterDecision.KEEP_ALL
            )
        
        # High user impact = keep more
        if user_patterns.affected_users > 1000:
            return SamplingDecision(
                sampling_rate=1.0,
                reason="High user impact",
                confidence=0.9,
                decision_type=FilterDecision.KEEP_ALL
            )
        
        # High cost-benefit ratio = keep more
        if cost_benefit.ratio > 0.8:
            return SamplingDecision(
                sampling_rate=0.8,
                reason="High cost-benefit ratio",
                confidence=0.8,
                decision_type=FilterDecision.KEEP_SOME
            )
        
        # Default adaptive sampling
        return SamplingDecision(
            sampling_rate=0.1,
            reason="Standard context-aware sampling",
            confidence=0.6,
            decision_type=FilterDecision.ADAPTIVE_SAMPLE
        )


class BusinessContextAnalyzer:
    """Analyzes business context of logs"""
    
    async def analyze_impact(self, log: 'LogEntry') -> BusinessImpact:
        """Analyze business impact of a log entry"""
        
        # Simple business impact analysis (in production, use more sophisticated methods)
        level = log.level
        message = log.message.lower()
        
        # Critical business keywords
        critical_keywords = ['payment', 'transaction', 'billing', 'security', 'compliance']
        high_keywords = ['user', 'customer', 'order', 'inventory']
        
        if any(keyword in message for keyword in critical_keywords):
            return BusinessImpact(level="critical", affected_users=1000, compliance_risk=True)
        elif any(keyword in message for keyword in high_keywords):
            return BusinessImpact(level="high", affected_users=100)
        elif level == 'ERROR':
            return BusinessImpact(level="medium", affected_users=10)
        else:
            return BusinessImpact(level="low", affected_users=1)


class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns"""
    
    async def analyze_patterns(self, log: 'LogEntry') -> UserPatterns:
        """Analyze user behavior patterns from log"""
        
        # Simple user behavior analysis (in production, use more sophisticated methods)
        message = log.message.lower()
        
        # Extract user-related information
        affected_users = 1  # Default
        
        if 'user' in message:
            # Try to extract user count
            import re
            user_matches = re.findall(r'(\d+)\s*users?', message)
            if user_matches:
                affected_users = int(user_matches[0])
            else:
                affected_users = 10  # Assume multiple users
        
        return UserPatterns(
            affected_users=affected_users,
            user_segments=['general'],
            peak_hours=self._is_peak_hours(),
            geographic_distribution={'global': affected_users}
        )
    
    def _is_peak_hours(self) -> bool:
        """Check if current time is peak hours"""
        now = datetime.utcnow()
        # Peak hours: 9 AM - 5 PM UTC
        return 9 <= now.hour < 17


class CostOptimizer:
    """Optimizes costs vs. value of log retention"""
    
    async def calculate_cost_benefit(self, log: 'LogEntry') -> CostBenefit:
        """Calculate cost-benefit ratio for log retention"""
        
        # Simple cost-benefit calculation (in production, use more sophisticated methods)
        level = log.level
        message = log.message.lower()
        
        # Storage cost (per log)
        storage_cost = 0.001  # $0.001 per log
        
        # Processing cost
        processing_cost = 0.0005  # $0.0005 per log
        
        # Debugging value
        debugging_value = 0.0
        if level == 'ERROR':
            debugging_value = 0.5
        elif level == 'WARNING':
            debugging_value = 0.3
        elif 'debug' in message or 'trace' in message:
            debugging_value = 0.1
        
        # Compliance value
        compliance_value = 0.0
        if any(keyword in message for keyword in ['audit', 'compliance', 'security']):
            compliance_value = 0.8
        
        return CostBenefit(
            storage_cost=storage_cost,
            processing_cost=processing_cost,
            debugging_value=debugging_value,
            compliance_value=compliance_value
        )
