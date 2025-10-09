import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.storage.database import get_db
from src.storage.models import Base, Service

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


def test_create_service():
    response = client.post(
        "/api/v1/services/",
        json={"team_id": 123, "name": "my-api"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["team_id"] == 123
    assert data["name"] == "my-api"
    assert data["is_active"] is True
    assert "id" in data


def test_get_service():
    create_response = client.post(
        "/api/v1/services/",
        json={"team_id": 123, "name": "test-service"},
    )
    service_id = create_response.json()["id"]

    response = client.get(f"/api/v1/services/{service_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == service_id
    assert data["name"] == "test-service"


def test_get_nonexistent_service_returns_404():
    response = client.get("/api/v1/services/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_services():
    client.post("/api/v1/services/", json={"team_id": 123, "name": "service-1"})
    client.post("/api/v1/services/", json={"team_id": 123, "name": "service-2"})
    client.post("/api/v1/services/", json={"team_id": 456, "name": "service-3"})

    response = client.get("/api/v1/services/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_list_services_filtered_by_team():
    client.post("/api/v1/services/", json={"team_id": 123, "name": "service-1"})
    client.post("/api/v1/services/", json={"team_id": 123, "name": "service-2"})
    client.post("/api/v1/services/", json={"team_id": 456, "name": "service-3"})

    response = client.get("/api/v1/services/?team_id=123")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(s["team_id"] == 123 for s in data)


@pytest.mark.parametrize(
    "team_id,service_name",
    [
        (1, "production-api"),
        (100, "staging-api"),
        (999, "test-microservice"),
    ],
)
def test_create_service_with_different_teams(team_id, service_name):
    response = client.post(
        "/api/v1/services/",
        json={"team_id": team_id, "name": service_name},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["team_id"] == team_id
    assert data["name"] == service_name
