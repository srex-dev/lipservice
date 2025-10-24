from dataclasses import dataclass
from datetime import datetime

from src.engine.anomaly_detector import Anomaly, AnomalyDetector
from src.engine.pattern_analyzer import LogEntry, PatternAnalysis, PatternAnalyzer


@dataclass
class AnalysisResult:
    """Complete analysis result including patterns and anomalies."""

    pattern_analysis: PatternAnalysis
    anomalies: list[Anomaly]
    summary: dict


class LogAnalyzer:
    """
    Complete log analysis pipeline.

    Combines pattern analysis and anomaly detection to provide
    comprehensive insights for AI policy generation.
    """

    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.anomaly_detector = AnomalyDetector()

    def analyze(self, logs: list[LogEntry], known_signatures: set[str] | None = None) -> AnalysisResult:
        """
        Perform complete analysis on logs.

        Args:
            logs: List of log entries to analyze
            known_signatures: Previously seen pattern signatures (for new pattern detection)

        Returns:
            AnalysisResult with patterns, anomalies, and summary
        """
        if not logs:
            return AnalysisResult(
                pattern_analysis=PatternAnalysis([], 0, 0, 0), anomalies=[], summary=self._empty_summary()
            )

        pattern_analysis = self.pattern_analyzer.analyze(logs)

        anomalies = self._detect_anomalies(pattern_analysis, logs, known_signatures or set())

        summary = self._generate_summary(pattern_analysis, anomalies, logs)

        return AnalysisResult(pattern_analysis=pattern_analysis, anomalies=anomalies, summary=summary)

    def _detect_anomalies(
        self, pattern_analysis: PatternAnalysis, logs: list[LogEntry], known_signatures: set[str]
    ) -> list[Anomaly]:
        """Detect all types of anomalies."""
        anomalies = []

        new_pattern_anomalies = self._detect_new_patterns(pattern_analysis, known_signatures)
        anomalies.extend(new_pattern_anomalies)

        error_anomalies = self._detect_error_surges(logs)
        anomalies.extend(error_anomalies)

        return anomalies

    def _detect_new_patterns(self, pattern_analysis: PatternAnalysis, known_signatures: set[str]) -> list[Anomaly]:
        """Detect new patterns that weren't seen before."""
        anomalies = []

        for cluster in pattern_analysis.clusters:
            if self.anomaly_detector.is_new_pattern(cluster.signature, known_signatures):
                anomalies.append(
                    Anomaly(
                        pattern_signature=cluster.signature,
                        anomaly_type="new_pattern",
                        severity="medium",
                        current_value=float(cluster.total_count),
                        baseline_value=0.0,
                        confidence=1.0,
                        detected_at=datetime.now(),
                        message=f"New pattern detected: {cluster.representative_message[:100]}",
                    )
                )

        return anomalies

    def _detect_error_surges(self, logs: list[LogEntry]) -> list[Anomaly]:
        """Detect surges in error-level logs."""
        error_logs = [log for log in logs if log.severity in ("ERROR", "CRITICAL")]

        if not error_logs:
            return []

        error_rate = len(error_logs) / len(logs)

        if error_rate > 0.1:
            return [
                Anomaly(
                    pattern_signature="error_rate",
                    anomaly_type="error_surge",
                    severity="high" if error_rate > 0.2 else "medium",
                    current_value=error_rate,
                    baseline_value=0.05,
                    confidence=min(error_rate * 5, 1.0),
                    detected_at=datetime.now(),
                    message=f"High error rate: {error_rate:.1%} of logs are errors",
                )
            ]

        return []

    def _generate_summary(
        self, pattern_analysis: PatternAnalysis, anomalies: list[Anomaly], logs: list[LogEntry]
    ) -> dict:
        """Generate summary statistics."""
        severity_counts = {}
        for log in logs:
            severity_counts[log.severity] = severity_counts.get(log.severity, 0) + 1

        return {
            "total_logs": len(logs),
            "unique_patterns": pattern_analysis.total_unique_patterns,
            "clusters_found": len(pattern_analysis.clusters),
            "anomalies_detected": len(anomalies),
            "high_severity_anomalies": len([a for a in anomalies if a.severity == "high"]),
            "severity_distribution": severity_counts,
            "error_rate": severity_counts.get("ERROR", 0) / len(logs) if logs else 0.0,
            "top_patterns": [
                {
                    "message": c.representative_message,
                    "count": c.total_count,
                    "signature": c.signature,
                }
                for c in sorted(pattern_analysis.clusters, key=lambda x: x.total_count, reverse=True)[:5]
            ],
        }

    def _empty_summary(self) -> dict:
        """Return empty summary for zero logs."""
        return {
            "total_logs": 0,
            "unique_patterns": 0,
            "clusters_found": 0,
            "anomalies_detected": 0,
            "high_severity_anomalies": 0,
            "severity_distribution": {},
            "error_rate": 0.0,
            "top_patterns": [],
        }

