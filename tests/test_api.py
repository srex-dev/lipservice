import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint_returns_service_info():
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "LipService"
    assert data["version"] == "0.1.0"
    assert data["status"] == "in development"


@pytest.mark.parametrize(
    "endpoint,expected_status",
    [
        ("/health", 200),
        ("/", 200),
        ("/nonexistent", 404),
    ],
)
def test_endpoint_status_codes(endpoint: str, expected_status: int):
    response = client.get(endpoint)
    assert response.status_code == expected_status
