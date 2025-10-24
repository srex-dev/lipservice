from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

from src.engine.signature import compute_signature


@dataclass
class LogEntry:
    """Represents a single log entry for analysis."""

    message: str
    severity: str
    timestamp: datetime
    service_name: str


@dataclass
class PatternCluster:
    """Represents a cluster of similar log patterns."""

    cluster_id: int
    size: int
    total_count: int
    representative_message: str
    signature: str
    severity_distribution: dict[str, int]
    first_seen: datetime
    last_seen: datetime


@dataclass
class PatternAnalysis:
    """Results of pattern analysis."""

    clusters: list[PatternCluster]
    noise_count: int
    total_unique_patterns: int
    total_logs: int


class PatternAnalyzer:
    """
    Analyzes log patterns to identify clusters and anomalies.
    
    Uses TF-IDF vectorization and DBSCAN clustering to group
    similar log messages together, enabling intelligent sampling.
    """

    def __init__(self, eps: float = 0.5, min_samples: int = 2):
        """
        Initialize pattern analyzer.
        
        Args:
            eps: DBSCAN epsilon parameter (distance threshold)
                 0.5 works well for typical log variations
            min_samples: Minimum cluster size
        """
        self.eps = eps
        self.min_samples = min_samples
        self.vectorizer = TfidfVectorizer(max_features=100, lowercase=True, stop_words="english")

    def analyze(self, logs: list[LogEntry]) -> PatternAnalysis:
        """
        Analyze logs to identify patterns and clusters.
        
        Args:
            logs: List of log entries to analyze
            
        Returns:
            PatternAnalysis with clusters and statistics
        """
        if not logs:
            return PatternAnalysis(clusters=[], noise_count=0, total_unique_patterns=0, total_logs=0)

        pattern_groups = self._group_by_signature(logs)

        if not pattern_groups:
            return PatternAnalysis(clusters=[], noise_count=0, total_unique_patterns=0, total_logs=len(logs))

        clusters = self._cluster_patterns(pattern_groups)

        return PatternAnalysis(
            clusters=clusters,
            noise_count=len([c for c in clusters if c.cluster_id == -1]),
            total_unique_patterns=len(pattern_groups),
            total_logs=len(logs),
        )

    def _group_by_signature(self, logs: list[LogEntry]) -> dict:
        """Group logs by signature and aggregate metadata."""
        groups = defaultdict(lambda: {"logs": [], "severity_dist": defaultdict(int)})

        for log in logs:
            sig = compute_signature(log.message)
            groups[sig]["logs"].append(log)
            groups[sig]["severity_dist"][log.severity] += 1

        return groups

    def _cluster_patterns(self, pattern_groups: dict) -> list[PatternCluster]:
        """Cluster patterns using DBSCAN."""
        if len(pattern_groups) < 2:
            return self._create_single_cluster(pattern_groups)

        signatures = list(pattern_groups.keys())
        messages = [pattern_groups[sig]["logs"][0].message for sig in signatures]

        try:
            vectors = self.vectorizer.fit_transform(messages)
            clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="cosine")
            labels = clustering.fit_predict(vectors.toarray())
        except Exception:
            return self._create_single_cluster(pattern_groups)

        clusters = []
        for label in set(labels):
            cluster_signatures = [sig for sig, lbl in zip(signatures, labels) if lbl == label]
            cluster = self._build_cluster(label, cluster_signatures, pattern_groups)
            clusters.append(cluster)

        return sorted(clusters, key=lambda c: c.total_count, reverse=True)

    def _create_single_cluster(self, pattern_groups: dict) -> list[PatternCluster]:
        """Create single cluster when clustering not possible."""
        signatures = list(pattern_groups.keys())
        return [self._build_cluster(0, signatures, pattern_groups)]

    def _build_cluster(self, cluster_id: int, signatures: list[str], pattern_groups: dict) -> PatternCluster:
        """Build cluster metadata from signatures."""
        all_logs = []
        severity_dist = defaultdict(int)

        for sig in signatures:
            all_logs.extend(pattern_groups[sig]["logs"])
            for severity, count in pattern_groups[sig]["severity_dist"].items():
                severity_dist[severity] += count

        representative = max(signatures, key=lambda s: len(pattern_groups[s]["logs"]))
        rep_message = pattern_groups[representative]["logs"][0].message

        return PatternCluster(
            cluster_id=cluster_id,
            size=len(signatures),
            total_count=len(all_logs),
            representative_message=rep_message,
            signature=representative,
            severity_distribution=dict(severity_dist),
            first_seen=min(log.timestamp for log in all_logs),
            last_seen=max(log.timestamp for log in all_logs),
        )

