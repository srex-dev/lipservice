from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import Policy, Service

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


class PolicyResponse(BaseModel):
    model_config = {"from_attributes": True}

    global_rate: float
    severity_rates: dict
    pattern_rates: dict
    anomaly_boost: float
    reasoning: str | None = None
    generated_by: str
    llm_model: str | None = None
    version: int


class PolicyHistoryItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    version: int
    global_rate: float
    severity_rates: dict
    generated_by: str
    is_active: bool
    created_at: datetime


@router.get("/{service_name}", response_model=PolicyResponse)
async def get_policy(service_name: str, team_id: int, db: Session = Depends(get_db)) -> PolicyResponse:
    """
    Get current active sampling policy for a service.
    This is called by SDKs to fetch sampling rules.
    """
    service = db.query(Service).filter(Service.name == service_name, Service.team_id == team_id).first()

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found for team {team_id}")

    active_policy = (
        db.query(Policy).filter(Policy.service_id == service.id, Policy.is_active == True).first()  # noqa: E712
    )

    if not active_policy:
        return _default_policy()

    return PolicyResponse.model_validate(active_policy)


@router.get("/{service_name}/history", response_model=list[PolicyHistoryItem])
async def get_policy_history(
    service_name: str, team_id: int, limit: int = 10, db: Session = Depends(get_db)
) -> list[PolicyHistoryItem]:
    """
    Get policy history for a service.
    Useful for debugging and understanding policy evolution.
    """
    service = db.query(Service).filter(Service.name == service_name, Service.team_id == team_id).first()

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    policies = (
        db.query(Policy)
        .filter(Policy.service_id == service.id)
        .order_by(Policy.version.desc())
        .limit(limit)
        .all()
    )

    return [PolicyHistoryItem.model_validate(p) for p in policies]


def _default_policy() -> PolicyResponse:
    """
    Return default conservative policy when no AI policy exists.
    Always keeps errors, samples INFO/DEBUG conservatively.
    """
    return PolicyResponse(
        global_rate=1.0,
        severity_rates={
            "DEBUG": 0.1,
            "INFO": 0.3,
            "WARNING": 0.7,
            "ERROR": 1.0,
            "CRITICAL": 1.0,
        },
        pattern_rates={},
        anomaly_boost=2.0,
        reasoning="Default policy - no AI analysis performed yet",
        generated_by="default",
        llm_model=None,
        version=0,
    )
