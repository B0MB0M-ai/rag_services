from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_envelope() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {
            "status": "ok",
            "service": "ai-service-repair-backend",
            "environment": "development",
            "mock_ai": True,
        },
    }
