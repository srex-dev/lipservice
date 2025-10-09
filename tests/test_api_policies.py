from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.storage.database import get_db
from src.storage.models import Base, Policy, Service

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


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_get_policy_returns_default_when_no_policy_exists():
    db = TestSessionLocal()
    service = Service(team_id=123, name="test-api")
    db.add(service)
    db.commit()
    db.close()

    response = client.get("/api/v1/policies/test-api?team_id=123")

    assert response.status_code == 200
    data = response.json()
    assert data["global_rate"] == 1.0
    assert data["severity_rates"]["ERROR"] == 1.0
    assert data["severity_rates"]["INFO"] == 0.3
    assert data["generated_by"] == "default"
    assert data["version"] == 0


def test_get_policy_returns_active_policy():
    db = TestSessionLocal()
    service = Service(team_id=123, name="test-api")
    db.add(service)
    db.commit()

    policy = Policy(
        service_id=service.id,
        version=1,
        global_rate=0.5,
        severity_rates={"ERROR": 1.0, "INFO": 0.1},
        pattern_rates={"pattern123": 0.05},
        anomaly_boost=3.0,
        reasoning="AI-generated policy for cost optimization",
        generated_by="llm",
        llm_model="gpt-4",
        is_active=True,
    )
    db.add(policy)
    db.commit()
    db.close()

    response = client.get("/api/v1/policies/test-api?team_id=123")

    assert response.status_code == 200
    data = response.json()
    assert data["global_rate"] == 0.5
    assert data["severity_rates"]["ERROR"] == 1.0
    assert data["severity_rates"]["INFO"] == 0.1
    assert data["pattern_rates"]["pattern123"] == 0.05
    assert data["anomaly_boost"] == 3.0
    assert data["generated_by"] == "llm"
    assert data["llm_model"] == "gpt-4"
    assert data["version"] == 1


def test_get_policy_for_nonexistent_service_returns_404():
    response = client.get("/api/v1/policies/nonexistent-service?team_id=123")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_policy_history():
    db = TestSessionLocal()
    service = Service(team_id=123, name="test-api")
    db.add(service)
    db.commit()

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
    db.add_all([policy_v1, policy_v2])
    db.commit()
    db.close()

    response = client.get("/api/v1/policies/test-api/history?team_id=123")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["version"] == 2
    assert data[1]["version"] == 1


def test_policy_history_respects_limit():
    db = TestSessionLocal()
    service = Service(team_id=123, name="test-api")
    db.add(service)
    db.commit()

    for i in range(5):
        policy = Policy(
            service_id=service.id,
            version=i + 1,
            global_rate=1.0 - (i * 0.1),
            severity_rates={"ERROR": 1.0},
            pattern_rates={},
            generated_by="llm",
            is_active=(i == 4),
        )
        db.add(policy)
    db.commit()
    db.close()

    response = client.get("/api/v1/policies/test-api/history?team_id=123&limit=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["version"] == 5
