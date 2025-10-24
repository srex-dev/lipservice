from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.integrations.analysis_service import AnalysisService
from src.integrations.posthog_client import PostHogLogsClient
from src.storage.database import get_db

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    """Request to analyze a service's logs from PostHog."""

    team_id: int
    service_name: str
    hours: int = 1
    clickhouse_host: str | None = None
    api_url: str | None = None
    api_key: str | None = None


class AnalyzeResponse(BaseModel):
    """Response from log analysis."""

    status: str
    total_logs: int
    unique_patterns: int
    clusters_found: int
    anomalies_detected: int
    error_rate: float
    top_patterns: list[dict]
    anomalies: list[dict]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_service_logs(request: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalyzeResponse:
    """
    Analyze logs for a service from PostHog.

    Fetches logs from PostHog, runs pattern analysis and anomaly detection,
    stores results in database for future policy generation.

    Args:
        request: Analysis request with PostHog credentials
        db: Database session

    Returns:
        Analysis results with patterns and anomalies
    """
    if not request.clickhouse_host and not (request.api_url and request.api_key):
        raise HTTPException(
            status_code=400, detail="Either clickhouse_host or (api_url + api_key) required"
        )

    posthog_client = PostHogLogsClient(
        clickhouse_host=request.clickhouse_host,
        api_url=request.api_url,
        api_key=request.api_key,
    )

    analysis_service = AnalysisService(posthog_client)

    try:
        result = await analysis_service.analyze_service(request.team_id, request.service_name, request.hours, db)

        return AnalyzeResponse(
            status="completed",
            total_logs=result.summary["total_logs"],
            unique_patterns=result.summary["unique_patterns"],
            clusters_found=result.summary["clusters_found"],
            anomalies_detected=result.summary["anomalies_detected"],
            error_rate=result.summary["error_rate"],
            top_patterns=result.summary["top_patterns"],
            anomalies=[
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "message": a.message,
                    "confidence": a.confidence,
                }
                for a in result.anomalies
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

