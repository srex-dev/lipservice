from datetime import datetime

import pytest

from src.storage.models import AnalysisRun, Pattern, Policy, Service


def test_service_creation(db_session):
    service = Service(team_id=123, name="test-api", is_active=True)
    db_session.add(service)
    db_session.commit()

    assert service.id is not None
    assert service.team_id == 123
    assert service.name == "test-api"
    assert service.is_active is True
    assert service.created_at is not None


def test_service_relationships(db_session):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    pattern = Pattern(
        service_id=service.id,
        signature="abc123",
        representative_message="User logged in",
        count=100,
        sampled_count=10,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
    )
    db_session.add(pattern)
    db_session.commit()

    assert len(service.patterns) == 1
    assert service.patterns[0].signature == "abc123"


def test_pattern_creation(db_session):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    pattern = Pattern(
        service_id=service.id,
        signature="def456",
        representative_message="Payment processed",
        count=50,
        sampled_count=25,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        severity_distribution={"ERROR": 10, "INFO": 40},
    )
    db_session.add(pattern)
    db_session.commit()

    assert pattern.id is not None
    assert pattern.signature == "def456"
    assert pattern.count == 50
    assert pattern.severity_distribution["ERROR"] == 10


@pytest.mark.parametrize(
    "global_rate,severity_rates,expected_generated_by",
    [
        (1.0, {"ERROR": 1.0, "INFO": 0.1}, "rule-based"),
        (0.5, {"ERROR": 1.0, "WARNING": 0.5, "INFO": 0.05}, "llm"),
        (0.8, {"ERROR": 1.0, "CRITICAL": 1.0, "DEBUG": 0.01}, "llm"),
    ],
)
def test_policy_creation_with_different_rates(db_session, global_rate, severity_rates, expected_generated_by):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    policy = Policy(
        service_id=service.id,
        global_rate=global_rate,
        severity_rates=severity_rates,
        pattern_rates={},
        generated_by=expected_generated_by,
        is_active=True,
    )
    db_session.add(policy)
    db_session.commit()

    assert policy.id is not None
    assert policy.global_rate == global_rate
    assert policy.severity_rates == severity_rates
    assert policy.generated_by == expected_generated_by


def test_policy_versioning(db_session):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    policy_v1 = Policy(
        service_id=service.id,
        version=1,
        global_rate=1.0,
        severity_rates={"ERROR": 1.0},
        pattern_rates={},
        generated_by="rule-based",
        is_active=False,
    )
    policy_v2 = Policy(
        service_id=service.id,
        version=2,
        global_rate=0.5,
        severity_rates={"ERROR": 1.0, "INFO": 0.1},
        pattern_rates={},
        generated_by="llm",
        is_active=True,
    )
    db_session.add_all([policy_v1, policy_v2])
    db_session.commit()

    assert len(service.policies) == 2
    active_policies = [p for p in service.policies if p.is_active]
    assert len(active_policies) == 1
    assert active_policies[0].version == 2


def test_analysis_run_lifecycle(db_session):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    run = AnalysisRun(
        service_id=service.id,
        status="running",
        logs_analyzed=0,
        patterns_found=0,
    )
    db_session.add(run)
    db_session.commit()

    assert run.id is not None
    assert run.status == "running"
    assert run.started_at is not None
    assert run.completed_at is None

    run.status = "completed"
    run.logs_analyzed = 10000
    run.patterns_found = 42
    run.anomalies_detected = 3
    run.policy_generated = True
    run.completed_at = datetime.now()
    db_session.commit()

    assert run.status == "completed"
    assert run.logs_analyzed == 10000
    assert run.patterns_found == 42


@pytest.mark.parametrize(
    "status,logs_analyzed,patterns_found",
    [
        ("completed", 1000, 10),
        ("completed", 10000, 50),
        ("failed", 500, 0),
        ("running", 0, 0),
    ],
)
def test_analysis_run_different_states(db_session, status, logs_analyzed, patterns_found):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    run = AnalysisRun(
        service_id=service.id,
        status=status,
        logs_analyzed=logs_analyzed,
        patterns_found=patterns_found,
    )
    db_session.add(run)
    db_session.commit()

    assert run.status == status
    assert run.logs_analyzed == logs_analyzed
    assert run.patterns_found == patterns_found


def test_cascade_delete_service_deletes_related(db_session):
    service = Service(team_id=123, name="test-api")
    db_session.add(service)
    db_session.commit()

    pattern = Pattern(
        service_id=service.id,
        signature="xyz789",
        representative_message="Test log",
        count=10,
        sampled_count=5,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
    )
    policy = Policy(
        service_id=service.id,
        global_rate=0.5,
        severity_rates={"ERROR": 1.0},
        pattern_rates={},
        generated_by="rule-based",
    )
    db_session.add_all([pattern, policy])
    db_session.commit()

    service_id = service.id
    db_session.delete(service)
    db_session.commit()

    assert db_session.query(Pattern).filter_by(service_id=service_id).count() == 0
    assert db_session.query(Policy).filter_by(service_id=service_id).count() == 0
