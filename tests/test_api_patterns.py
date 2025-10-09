import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.storage.database import get_db
from src.storage.models import AnalysisRun, Base, Service

TEST_DATABASE_URL = "postgresql://lipservice:lipservice@localhost:5433/lipservice_test"

engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_receive_pattern_stats_creates_service_if_not_exists():
    now = time.time()
    response = client.post(
        "/api/v1/patterns/stats",
        json={
            "service_name": "new-api",
            "team_id": 123,
            "timestamp": now,
            "patterns": [
                {
                    "signature": "abc123",
                    "count": 100,
                    "sampled_count": 10,
                    "first_seen": now - 3600,
                    "last_seen": now,
                }
            ],
            "total_logs": 1000,
            "unique_patterns": 50,
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "queued" in data["message"].lower()
    assert data["analysis_run_id"] is not None

    db = TestSessionLocal()
    service = db.query(Service).filter(Service.name == "new-api").first()
    assert service is not None
    assert service.team_id == 123
    db.close()


def test_receive_pattern_stats_creates_analysis_run():
    db = TestSessionLocal()
    service = Service(team_id=123, name="existing-api")
    db.add(service)
    db.commit()
    db.close()

    now = time.time()
    response = client.post(
        "/api/v1/patterns/stats",
        json={
            "service_name": "existing-api",
            "team_id": 123,
            "timestamp": now,
            "patterns": [{"signature": "sig1", "count": 50, "sampled_count": 5, "first_seen": now, "last_seen": now}],
            "total_logs": 500,
            "unique_patterns": 25,
        },
    )

    assert response.status_code == 202

    db = TestSessionLocal()
    analysis_run = db.query(AnalysisRun).first()
    assert analysis_run is not None
    assert analysis_run.status == "pending"
    assert analysis_run.logs_analyzed == 500
    assert analysis_run.patterns_found == 25
    db.close()


@pytest.mark.parametrize(
    "total_logs,unique_patterns",
    [
        (1000, 10),
        (10000, 100),
        (100000, 500),
    ],
)
def test_receive_pattern_stats_with_different_volumes(total_logs, unique_patterns):
    db = TestSessionLocal()
    service = Service(team_id=123, name="test-api")
    db.add(service)
    db.commit()
    db.close()

    now = time.time()
    response = client.post(
        "/api/v1/patterns/stats",
        json={
            "service_name": "test-api",
            "team_id": 123,
            "timestamp": now,
            "patterns": [],
            "total_logs": total_logs,
            "unique_patterns": unique_patterns,
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"

    db = TestSessionLocal()
    analysis_run = db.query(AnalysisRun).first()
    assert analysis_run.logs_analyzed == total_logs
    assert analysis_run.patterns_found == unique_patterns
    db.close()


def test_pattern_stats_metadata_stored_correctly():
    db = TestSessionLocal()
    service = Service(team_id=123, name="test-api")
    db.add(service)
    db.commit()
    db.close()

    now = time.time()
    response = client.post(
        "/api/v1/patterns/stats",
        json={
            "service_name": "test-api",
            "team_id": 123,
            "timestamp": now,
            "patterns": [
                {"signature": "s1", "count": 10, "sampled_count": 1, "first_seen": now, "last_seen": now},
                {"signature": "s2", "count": 20, "sampled_count": 2, "first_seen": now, "last_seen": now},
            ],
            "total_logs": 100,
            "unique_patterns": 10,
        },
    )

    assert response.status_code == 202

    db = TestSessionLocal()
    analysis_run = db.query(AnalysisRun).first()
    assert analysis_run.run_metadata is not None
    assert analysis_run.run_metadata["pattern_count"] == 2
    assert analysis_run.run_metadata["source"] == "sdk_upload"
    db.close()
