"""
Adaptive Log Filtering API endpoints
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field


class LogContext:
    """Simple log context for API"""
    
    def __init__(self, **kwargs):
        self.data = kwargs
    
    def __repr__(self):
        return f"LogContext({self.data})"

router = APIRouter(prefix="/api/v1/adaptive-filtering", tags=["adaptive-filtering"])


# Data Models
class LogEntry(BaseModel):
    """Log entry for filtering"""
    id: UUID
    timestamp: datetime
    level: str
    message: str
    service_name: str
    context: Optional[LogContext] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FilterContext(BaseModel):
    """Context for filtering decisions"""
    base_sampling_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    service_name: Optional[str] = None
    user_impact_threshold: int = Field(default=1000, ge=0)
    cost_threshold: float = Field(default=100.0, ge=0.0)


class SamplingDecision(BaseModel):
    """Decision about log sampling"""
    sampling_rate: float = Field(ge=0.0, le=1.0)
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    decision_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EnvironmentState(BaseModel):
    """Current state of the environment"""
    incident_active: bool = False
    deployment_active: bool = False
    high_error_rate: bool = False
    low_traffic: bool = False
    business_hours: bool = False
    weekend: bool = False
    cpu_usage: float = Field(ge=0.0, le=1.0)
    memory_usage: float = Field(ge=0.0, le=1.0)
    error_count: int = Field(ge=0)
    total_logs: int = Field(ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class FilterRequest(BaseModel):
    """Request for adaptive filtering"""
    logs: List[LogEntry]
    context: FilterContext
    analysis_types: List[str] = Field(default=["adaptive_filtering", "pattern_learning"])


class FilterResponse(BaseModel):
    """Response from adaptive filtering"""
    decisions: List[SamplingDecision]
    environment_state: EnvironmentState
    adaptations: List[str] = Field(default_factory=list)
    processing_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PatternLearningRequest(BaseModel):
    """Request for pattern learning"""
    logs: List[LogEntry]
    time_window: Optional[timedelta] = None


class PatternLearningResponse(BaseModel):
    """Response from pattern learning"""
    new_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    adaptations: List[str] = Field(default_factory=list)
    confidence_score: float
    processing_time: float


# API Endpoints
@router.post("/filter", response_model=FilterResponse)
async def adaptive_filter_logs(request: FilterRequest):
    """
    Apply adaptive filtering to logs based on environment context.
    
    This endpoint analyzes the current environment state and applies
    intelligent filtering decisions to the provided logs.
    """
    try:
        from src.adaptive_filtering import AdaptiveLogFilter, EnvironmentContext
        
        filter_engine = AdaptiveLogFilter()
        env_context = EnvironmentContext()
        
        # Get current environment state
        env_state = await env_context.get_current_state()
        
        # Apply adaptive filtering to each log
        decisions = []
        start_time = datetime.utcnow()
        
        for log in request.logs:
            decision = await filter_engine.adaptive_filter(log, request.context)
            decisions.append(decision)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return FilterResponse(
            decisions=decisions,
            environment_state=env_state,
            adaptations=[],  # Would be populated by learning engine
            processing_time=processing_time,
            metadata={
                'total_logs': len(request.logs),
                'filter_types': request.analysis_types
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptive filtering failed: {str(e)}")


@router.post("/learn-patterns", response_model=PatternLearningResponse)
async def learn_patterns(request: PatternLearningRequest):
    """
    Learn new patterns from logs and adapt filtering strategies.
    
    This endpoint analyzes logs to detect new patterns and adapts
    the filtering system accordingly.
    """
    try:
        from src.adaptive_filtering import DynamicPatternLearner
        
        learner = DynamicPatternLearner()
        
        start_time = datetime.utcnow()
        result = await learner.learn_and_adapt(request.logs)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Convert patterns to dict format for JSON serialization
        pattern_dicts = []
        for pattern in result.new_patterns:
            pattern_dicts.append({
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'frequency': pattern.frequency,
                'last_seen': pattern.last_seen,
                'confidence': pattern.confidence
            })
        
        return PatternLearningResponse(
            new_patterns=pattern_dicts,
            adaptations=result.adaptations,
            confidence_score=result.confidence_score,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern learning failed: {str(e)}")


@router.get("/environment-state", response_model=EnvironmentState)
async def get_environment_state():
    """
    Get current environment state for filtering decisions.
    """
    try:
        from src.adaptive_filtering import EnvironmentContext
        
        env_context = EnvironmentContext()
        env_state = await env_context.get_current_state()
        
        return env_state
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get environment state: {str(e)}")


@router.post("/context-aware-sample", response_model=List[SamplingDecision])
async def context_aware_sample(
    logs: List[LogEntry],
    context: FilterContext
):
    """
    Apply context-aware sampling considering business impact and user behavior.
    """
    try:
        from src.adaptive_filtering import ContextAwareSampler
        
        sampler = ContextAwareSampler()
        
        decisions = []
        for log in logs:
            decision = await sampler.context_aware_sample(log)
            decisions.append(decision)
        
        return decisions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context-aware sampling failed: {str(e)}")


@router.get("/filter-performance")
async def get_filter_performance():
    """
    Get performance metrics for the adaptive filtering system.
    """
    try:
        from lipservice.adaptive_filtering import PerformanceTracker
        
        # Mock performance data (in production, this would come from real metrics)
        performance_data = {
            'total_decisions': 1000,
            'correct_decisions': 850,
            'false_positives': 50,
            'false_negatives': 100,
            'accuracy': 0.85,
            'precision': 0.94,
            'recall': 0.89,
            'f1_score': 0.91
        }
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/optimize-configuration")
async def optimize_configuration(
    current_config: FilterContext,
    performance_metrics: Dict[str, Any]
):
    """
    Automatically optimize filtering configuration based on performance metrics.
    """
    try:
        from lipservice.adaptive_filtering import SmartConfigurationManager
        
        optimizer = SmartConfigurationManager()
        
        # Mock optimization (in production, this would use real optimization)
        optimized_config = FilterContext(
            base_sampling_rate=current_config.base_sampling_rate * 0.8,  # Reduce sampling
            service_name=current_config.service_name,
            user_impact_threshold=current_config.user_impact_threshold,
            cost_threshold=current_config.cost_threshold * 1.2  # Increase cost threshold
        )
        
        return {
            'original_config': current_config,
            'optimized_config': optimized_config,
            'expected_improvements': {
                'cost_reduction': 0.2,
                'accuracy_improvement': 0.05,
                'performance_gain': 0.15
            },
            'confidence': 0.8
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration optimization failed: {str(e)}")


@router.post("/real-time-adapt")
async def real_time_adapt(
    current_state: EnvironmentState,
    adaptation_threshold: float = Query(default=0.7, ge=0.0, le=1.0)
):
    """
    Perform real-time adaptation based on current system state.
    """
    try:
        from lipservice.adaptive_filtering import RealTimeAdapter
        
        adapter = RealTimeAdapter()
        
        # Mock real-time adaptation
        adaptations = []
        
        if current_state.incident_active:
            adaptations.append("Increase sampling rate due to active incident")
        if current_state.high_error_rate:
            adaptations.append("Increase error log retention")
        if current_state.low_traffic:
            adaptations.append("Reduce sampling during low traffic")
        
        return {
            'adaptations': adaptations,
            'new_sampling_rate': 0.1 if not current_state.incident_active else 0.3,
            'confidence': 0.9,
            'applied_at': datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real-time adaptation failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for adaptive filtering service"""
    return {
        "status": "healthy",
        "service": "adaptive-filtering",
        "timestamp": datetime.utcnow()
    }
