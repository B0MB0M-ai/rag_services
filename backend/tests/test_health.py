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


def test_home_page_is_served_by_fastapi() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "เริ่มต้นด้วยข้อมูล" in response.text
    assert "htmx.org" in response.text
    assert "alpinejs" in response.text


def test_health_status_partial_reports_runtime_configuration() -> None:
    response = TestClient(app).get("/partials/health-status")

    assert response.status_code == 200
    assert "Backend operational" in response.text
    assert "Environment: development" in response.text
