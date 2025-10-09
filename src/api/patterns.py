from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import AnalysisRun, Service

router = APIRouter(prefix="/api/v1/patterns", tags=["patterns"])


class PatternStat(BaseModel):
    """Pattern statistics from SDK."""

    signature: str
    count: int
    sampled_count: int
    first_seen: float  # Unix timestamp
    last_seen: float  # Unix timestamp


class PatternStatsRequest(BaseModel):
    """Pattern statistics upload from SDK."""

    service_name: str
    team_id: int
    timestamp: float
    patterns: list[PatternStat]
    total_logs: int
    unique_patterns: int


class PatternStatsResponse(BaseModel):
    """Response after receiving pattern stats."""

    status: str
    message: str
    analysis_run_id: int | None = None


@router.post("/stats", response_model=PatternStatsResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_pattern_stats(stats: PatternStatsRequest, db: Session = Depends(get_db)) -> PatternStatsResponse:
    """
    Receive pattern statistics from SDK.
    This triggers async analysis and policy generation.

    Called by SDKs periodically (e.g., every 15 minutes) to upload
    local pattern statistics for AI analysis.
    """
    service = db.query(Service).filter(Service.name == stats.service_name, Service.team_id == stats.team_id).first()

    if not service:
        service = Service(team_id=stats.team_id, name=stats.service_name, is_active=True)
        db.add(service)
        db.commit()
        db.refresh(service)

    analysis_run = AnalysisRun(
        service_id=service.id,
        status="pending",
        logs_analyzed=stats.total_logs,
        patterns_found=stats.unique_patterns,
        run_metadata={
            "pattern_count": len(stats.patterns),
            "source": "sdk_upload",
            "timestamp": stats.timestamp,
        },
    )
    db.add(analysis_run)
    db.commit()
    db.refresh(analysis_run)

    return PatternStatsResponse(
        status="accepted",
        message=f"Pattern stats received for {stats.service_name}. Analysis queued.",
        analysis_run_id=analysis_run.id,
    )
