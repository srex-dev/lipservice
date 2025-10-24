import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.engine.llm_provider import AnthropicProvider, OpenAIProvider, RuleBasedProvider
from src.engine.policy_generator import PolicyGenerator
from src.integrations.analysis_service import AnalysisService
from src.integrations.posthog_client import PostHogLogsClient
from src.storage.database import get_db
from src.storage.models import Policy, Service

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


class GeneratePolicyRequest(BaseModel):
    """Request to analyze logs and generate policy."""

    team_id: int
    service_name: str
    hours: int = 1
    clickhouse_host: str | None = None
    api_url: str | None = None
    api_key: str | None = None
    llm_provider: str = "rule-based"  # 'openai', 'anthropic', 'rule-based'
    cost_target: float | None = None


class GeneratePolicyResponse(BaseModel):
    """Response with generated policy."""

    status: str
    policy_id: int
    policy_version: int
    global_rate: float
    severity_rates: dict
    pattern_rates: dict
    anomaly_boost: float
    reasoning: str
    generated_by: str
    analysis_summary: dict


@router.post("/generate-policy", response_model=GeneratePolicyResponse)
async def generate_policy_from_logs(
    request: GeneratePolicyRequest, db: Session = Depends(get_db)
) -> GeneratePolicyResponse:
    """
    Complete pipeline: Fetch logs from PostHog → Analyze → Generate AI policy.

    This is the core end-to-end workflow that demonstrates LipService's value:
    1. Fetch logs from PostHog
    2. Analyze patterns and anomalies
    3. Use LLM to generate intelligent sampling policy
    4. Store policy in database
    5. Return policy for SDK to use

    Args:
        request: Pipeline request with PostHog and LLM configuration
        db: Database session

    Returns:
        Generated policy with analysis summary
    """
    if not request.clickhouse_host and not (request.api_url and request.api_key):
        raise HTTPException(status_code=400, detail="PostHog credentials required")

    posthog_client = PostHogLogsClient(
        clickhouse_host=request.clickhouse_host, api_url=request.api_url, api_key=request.api_key
    )

    analysis_service = AnalysisService(posthog_client)

    try:
        analysis_result = await analysis_service.analyze_service(
            request.team_id, request.service_name, request.hours, db
        )

        llm_provider = _get_llm_provider(request.llm_provider)
        policy_generator = PolicyGenerator(llm_provider)

        policy_response = await policy_generator.generate_policy(
            request.service_name, analysis_result, request.cost_target
        )

        service = db.query(Service).filter(Service.team_id == request.team_id, Service.name == request.service_name).first()

        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        existing_policies = db.query(Policy).filter(Policy.service_id == service.id).all()
        for p in existing_policies:
            p.is_active = False

        next_version = max([p.version for p in existing_policies], default=0) + 1

        new_policy = Policy(
            service_id=service.id,
            version=next_version,
            global_rate=policy_response.global_rate,
            severity_rates=policy_response.severity_rates,
            pattern_rates=policy_response.pattern_rates,
            anomaly_boost=policy_response.anomaly_boost,
            reasoning=policy_response.reasoning,
            generated_by="llm" if request.llm_provider != "rule-based" else "rule-based",
            llm_model=policy_response.model,
            is_active=True,
        )
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)

        return GeneratePolicyResponse(
            status="success",
            policy_id=new_policy.id,
            policy_version=new_policy.version,
            global_rate=new_policy.global_rate,
            severity_rates=new_policy.severity_rates,
            pattern_rates=new_policy.pattern_rates,
            anomaly_boost=new_policy.anomaly_boost,
            reasoning=new_policy.reasoning or "",
            generated_by=new_policy.generated_by,
            analysis_summary=analysis_result.summary,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


def _get_llm_provider(provider_name: str):
    """Get LLM provider instance based on configuration."""
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        return OpenAIProvider(api_key=api_key)

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        return AnthropicProvider(api_key=api_key)

    elif provider_name == "rule-based":
        return RuleBasedProvider()

    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")

