"""
Generate realistic PostHog-style logs for testing.

Based on PostHog's actual usage patterns observed in their codebase.
"""

import random
import time
from datetime import datetime, timedelta

# PostHog-style log patterns observed from codebase
POSTHOG_LOG_PATTERNS = {
    "DEBUG": [
        "Cache hit for key session_{uuid}",
        "Cache miss for key project_{id}",
        "Database query executed in {ms}ms",
        "Redis connection pool size: {num}",
        "Celery task {task_name} started",
        "Feature flag {flag_name} evaluated for team {team_id}",
        "HogQL query parsed successfully",
        "Property definition lookup for {property}",
        "Event ingestion queue size: {size}",
        "ClickHouse connection established",
    ],
    "INFO": [
        "User {user_id} authenticated via {method}",
        "API request GET /api/projects/{id}/insights completed in {ms}ms",
        "Team {team_id} feature flags refreshed",
        "Dashboard {dashboard_id} loaded by user {user_id}",
        "Query executed: returned {count} results in {ms}ms",
        "Replay capture received for session {session_id}",
        "Event batch processed: {count} events",
        "Cohort {cohort_id} recalculated",
        "Insight {insight_id} computed successfully",
        "Plugin {plugin_id} executed for team {team_id}",
    ],
    "WARNING": [
        "Slow query detected: {query} took {ms}ms",
        "High memory usage: {percent}%",
        "ClickHouse connection pool near capacity",
        "Celery queue backlog: {count} tasks",
        "Rate limit approaching for team {team_id}",
        "Large result set returned: {count} rows",
        "Plugin {plugin_id} execution timeout",
        "Feature flag evaluation cache miss",
        "Database migration pending",
        "Kafka lag detected: {seconds}s behind",
    ],
    "ERROR": [
        "Failed to execute query: {error}",
        "Database connection timeout for team {team_id}",
        "ClickHouse query failed: {reason}",
        "Event ingestion error: {error}",
        "Plugin {plugin_id} crashed: {error}",
        "Failed to load dashboard {dashboard_id}",
        "Authentication failed for user {user_id}",
        "Cohort calculation failed: {reason}",
        "Feature flag evaluation error",
        "Insight computation timeout",
    ],
    "CRITICAL": [
        "ClickHouse connection lost",
        "Redis cluster unreachable",
        "Kafka broker offline",
        "Critical memory threshold exceeded",
        "Database connection pool exhausted",
    ],
}


def generate_posthog_logs(
    num_logs: int = 1000,
    duration_hours: int = 1,
    team_id: int = 1,
) -> list[dict]:
    """
    Generate realistic PostHog-style logs.
    
    Args:
        num_logs: Number of logs to generate
        duration_hours: Time span for logs
        team_id: PostHog team ID
        
    Returns:
        List of log dictionaries with PostHog schema
    """
    logs = []
    start_time = datetime.now() - timedelta(hours=duration_hours)
    
    # Distribution based on typical PostHog usage
    severity_weights = {
        "DEBUG": 0.40,    # 40% debug (cache, queries)
        "INFO": 0.40,     # 40% info (API requests, events)
        "WARNING": 0.15,  # 15% warnings (slow queries)
        "ERROR": 0.04,    # 4% errors
        "CRITICAL": 0.01, # 1% critical
    }
    
    for i in range(num_logs):
        # Random severity based on weights
        severity = random.choices(
            list(severity_weights.keys()),
            weights=list(severity_weights.values())
        )[0]
        
        # Random pattern for this severity
        pattern = random.choice(POSTHOG_LOG_PATTERNS[severity])
        
        # Fill in variables
        message = pattern.format(
            uuid=f"{random.randint(1000, 9999)}",
            id=random.randint(1, 100),
            ms=random.randint(10, 5000),
            num=random.randint(1, 50),
            task_name=random.choice(["calculate_cohort", "process_event", "sync_feature_flags"]),
            team_id=team_id,
            flag_name=random.choice(["new-dashboard", "beta-feature", "ab-test-v2"]),
            property=random.choice(["$current_url", "$browser", "$device_type"]),
            size=random.randint(0, 10000),
            user_id=random.randint(1, 1000),
            method=random.choice(["personal_api_key", "session", "sso"]),
            dashboard_id=random.randint(1, 50),
            count=random.randint(1, 10000),
            session_id=f"session-{random.randint(10000, 99999)}",
            insight_id=random.randint(1, 200),
            plugin_id=random.randint(1, 20),
            cohort_id=random.randint(1, 30),
            query="SELECT * FROM events WHERE ...",
            percent=random.randint(70, 95),
            seconds=random.randint(1, 300),
            error=random.choice([
                "timeout",
                "connection refused",
                "invalid syntax",
                "permission denied"
            ]),
            reason=random.choice([
                "timeout exceeded",
                "invalid parameters",
                "resource not found"
            ]),
        )
        
        # Random timestamp within duration
        timestamp = start_time + timedelta(
            seconds=random.randint(0, duration_hours * 3600)
        )
        
        # PostHog log schema
        log = {
            "team_id": team_id,
            "timestamp": timestamp.isoformat(),
            "severity_text": severity,
            "severity_number": {
                "DEBUG": 5,
                "INFO": 9,
                "WARNING": 13,
                "ERROR": 17,
                "CRITICAL": 21,
            }[severity],
            "service_name": random.choice([
                "web",
                "worker",
                "plugins",
                "async-migrations",
                "celery",
            ]),
            "body": message,
            "attributes": {
                "team_id": str(team_id),
                "environment": "production",
                "version": "1.0.0",
            },
        }
        
        logs.append(log)
    
    # Sort by timestamp
    logs.sort(key=lambda x: x["timestamp"])
    
    return logs


def print_log_distribution(logs: list[dict]) -> None:
    """Print distribution statistics."""
    from collections import defaultdict
    
    severity_counts = defaultdict(int)
    service_counts = defaultdict(int)
    
    for log in logs:
        severity_counts[log["severity_text"]] += 1
        service_counts[log["service_name"]] += 1
    
    print("\n📊 Generated Log Distribution:")
    print("-" * 60)
    print("\nBy Severity:")
    for severity, count in sorted(severity_counts.items()):
        pct = count / len(logs) * 100
        print(f"  {severity:10s}: {count:5d} logs ({pct:5.1f}%)")
    
    print("\nBy Service:")
    for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(logs) * 100
        print(f"  {service:20s}: {count:5d} logs ({pct:5.1f}%)")
    
    print("\nSample Messages:")
    for i, log in enumerate(logs[:5], 1):
        print(f"\n  {i}. [{log['severity_text']:8s}] {log['service_name']}")
        print(f"     {log['body'][:70]}...")


if __name__ == "__main__":
    print("🎙️ PostHog-Style Log Generator")
    print("=" * 60)
    
    # Generate 1000 logs over 1 hour
    logs = generate_posthog_logs(num_logs=1000, duration_hours=1, team_id=1)
    
    print_log_distribution(logs)
    
    # Save to file
    import json
    output_file = "posthog_test_logs.json"
    with open(output_file, "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"\n✅ Saved {len(logs)} logs to {output_file}")
    print("\nUse with LipService:")
    print(f"  python tests/integration/test_with_generated_logs.py --file {output_file}")

