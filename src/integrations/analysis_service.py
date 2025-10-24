import structlog
from sqlalchemy.orm import Session

from src.engine.analyzer import AnalysisResult, LogAnalyzer
from src.integrations.posthog_client import PostHogLogsClient
from src.storage.models import AnalysisRun, Pattern, Service

logger = structlog.get_logger(__name__)


class AnalysisService:
    """
    Orchestrates log analysis from PostHog.

    Fetches logs from PostHog, analyzes patterns, stores results,
    and prepares data for AI policy generation.
    """

    def __init__(self, posthog_client: PostHogLogsClient):
        self.posthog_client = posthog_client
        self.analyzer = LogAnalyzer()

    async def analyze_service(
        self, team_id: int, service_name: str, hours: int, db: Session
    ) -> AnalysisResult:
        """
        Analyze logs for a service from PostHog.

        Args:
            team_id: PostHog team ID
            service_name: Service to analyze
            hours: Hours of logs to fetch
            db: Database session

        Returns:
            AnalysisResult with patterns and anomalies
        """
        service = db.query(Service).filter(Service.team_id == team_id, Service.name == service_name).first()

        if not service:
            service = Service(team_id=team_id, name=service_name, is_active=True)
            db.add(service)
            db.commit()
            db.refresh(service)

        analysis_run = AnalysisRun(service_id=service.id, status="running")
        db.add(analysis_run)
        db.commit()

        try:
            logs = await self.posthog_client.fetch_logs(team_id, service_name, hours)

            logger.info("Analyzing logs", service=service_name, log_count=len(logs))

            known_sigs = self._get_known_signatures(db, service.id)
            result = self.analyzer.analyze(logs, known_signatures=known_sigs)

            self._store_patterns(db, service.id, result)

            analysis_run.status = "completed"
            analysis_run.logs_analyzed = len(logs)
            analysis_run.patterns_found = result.pattern_analysis.total_unique_patterns
            analysis_run.anomalies_detected = len(result.anomalies)
            db.commit()

            logger.info(
                "Analysis complete",
                service=service_name,
                patterns=result.pattern_analysis.total_unique_patterns,
                anomalies=len(result.anomalies),
            )

            return result

        except Exception as e:
            analysis_run.status = "failed"
            analysis_run.error_message = str(e)
            db.commit()

            logger.error("Analysis failed", service=service_name, error=str(e))
            raise

    def _get_known_signatures(self, db: Session, service_id: int) -> set[str]:
        """Get previously seen pattern signatures for new pattern detection."""
        patterns = db.query(Pattern).filter(Pattern.service_id == service_id).all()
        return {p.signature for p in patterns}

    def _store_patterns(self, db: Session, service_id: int, result: AnalysisResult) -> None:
        """Store or update patterns in database."""
        for cluster in result.pattern_analysis.clusters:
            existing = db.query(Pattern).filter(Pattern.signature == cluster.signature).first()

            if existing:
                existing.count += cluster.total_count
                existing.last_seen = cluster.last_seen
                existing.severity_distribution = cluster.severity_distribution
            else:
                pattern = Pattern(
                    service_id=service_id,
                    signature=cluster.signature,
                    representative_message=cluster.representative_message,
                    count=cluster.total_count,
                    sampled_count=0,
                    first_seen=cluster.first_seen,
                    last_seen=cluster.last_seen,
                    severity_distribution=cluster.severity_distribution,
                )
                db.add(pattern)

        db.commit()
        logger.info("Stored patterns", service_id=service_id, pattern_count=len(result.pattern_analysis.clusters))

