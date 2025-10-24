"""
Demo: Pattern Analysis Engine

Shows how LipService analyzes logs to detect patterns and anomalies.
This is the core intelligence that enables smart sampling.
"""

from datetime import datetime, timedelta

from src.engine.analyzer import LogAnalyzer
from src.engine.pattern_analyzer import LogEntry


def main():
    """Run pattern analysis demo."""
    print("🎙️ LipService Pattern Analysis Demo\n")
    print("=" * 60)

    logs = generate_sample_logs()

    print(f"\n📊 Analyzing {len(logs)} log entries...\n")

    analyzer = LogAnalyzer()
    result = analyzer.analyze(logs)

    print("📈 Analysis Results:")
    print("-" * 60)
    print(f"Total Logs: {result.summary['total_logs']}")
    print(f"Unique Patterns: {result.summary['unique_patterns']}")
    print(f"Clusters Found: {result.summary['clusters_found']}")
    print(f"Anomalies Detected: {result.summary['anomalies_detected']}")
    print(f"Error Rate: {result.summary['error_rate']:.1%}")

    print("\n🔝 Top Patterns:")
    print("-" * 60)
    for i, pattern in enumerate(result.summary["top_patterns"][:5], 1):
        print(f"{i}. {pattern['message'][:60]}... (count: {pattern['count']})")

    print("\n⚠️  Anomalies Detected:")
    print("-" * 60)
    for anomaly in result.anomalies:
        print(f"[{anomaly.severity.upper()}] {anomaly.anomaly_type}: {anomaly.message}")
        print(f"   Confidence: {anomaly.confidence:.2f}")

    print("\n📊 Severity Distribution:")
    print("-" * 60)
    for severity, count in result.summary["severity_distribution"].items():
        bar = "█" * int(count / 10)
        print(f"{severity:8s}: {bar} {count}")

    print("\n💡 Sampling Recommendations:")
    print("-" * 60)
    print("Based on this analysis, LipService would recommend:")
    for cluster in result.pattern_analysis.clusters[:3]:
        error_pct = cluster.severity_distribution.get("ERROR", 0) / cluster.total_count * 100
        if error_pct > 10:
            rate = 1.0
            reason = "High error rate"
        elif cluster.total_count > 50:
            rate = 0.1
            reason = "Very frequent, low value"
        else:
            rate = 0.5
            reason = "Moderate frequency"

        print(f"Pattern: {cluster.representative_message[:50]}...")
        print(f"  → Sample at {rate:.0%} ({reason})")

    print("\n✨ This intelligence enables 50-80% cost savings!")
    print("=" * 60)


def generate_sample_logs() -> list[LogEntry]:
    """Generate realistic sample logs for demo."""
    now = datetime.now()
    logs = []

    for i in range(100):
        logs.append(LogEntry(f"User {i} logged in successfully", "INFO", now + timedelta(seconds=i), "web-api"))

    for i in range(50):
        logs.append(
            LogEntry(f"Payment ${i*10}.99 processed successfully", "INFO", now + timedelta(seconds=100 + i), "web-api")
        )

    for i in range(20):
        logs.append(
            LogEntry(f"Cache hit for key user_{i}", "DEBUG", now + timedelta(seconds=150 + i), "web-api")
        )

    for i in range(10):
        logs.append(
            LogEntry("Database connection timeout after 30s", "ERROR", now + timedelta(seconds=170 + i), "web-api")
        )

    for i in range(5):
        logs.append(LogEntry("API rate limit exceeded", "WARNING", now + timedelta(seconds=180 + i), "web-api"))

    logs.append(LogEntry("OutOfMemoryError: Heap space", "CRITICAL", now + timedelta(seconds=190), "web-api"))

    return logs


if __name__ == "__main__":
    main()

