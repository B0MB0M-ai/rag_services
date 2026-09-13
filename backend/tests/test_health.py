from fastapi.testclient import TestClient

from app.api.v1.routes import health
from app.core.config import Settings
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
            "ai_provider": "deterministic",
            "ai_model": None,
            "ai_ready": True,
            "openai_api_key_configured": False,
        },
    }


def test_home_page_is_served_by_fastapi() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Start with data" in response.text
    assert "htmx.org" in response.text
    assert "alpinejs" in response.text


def test_health_status_partial_reports_runtime_configuration() -> None:
    response = TestClient(app).get("/partials/health-status")

    assert response.status_code == 200
    assert "Backend operational" in response.text
    assert "Environment: development" in response.text
    assert "AI: deterministic" in response.text
    assert "ready" in response.text


def test_health_check_reports_effective_openai_configuration(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        mock_ai=False,
        openai_api_key="test-key",
        openai_response_model="gpt-5-mini",
    )
    monkeypatch.setattr(health, "get_settings", lambda: settings)

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert {
        key: data[key]
        for key in (
            "ai_provider",
            "ai_model",
            "ai_ready",
            "openai_api_key_configured",
        )
    } == {
        "ai_provider": "openai",
        "ai_model": "gpt-5-mini",
        "ai_ready": True,
        "openai_api_key_configured": True,
    }


def test_health_check_reports_missing_openai_key(monkeypatch) -> None:
    settings = Settings(_env_file=None, mock_ai=False, openai_api_key=None)
    monkeypatch.setattr(health, "get_settings", lambda: settings)

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"]["ai_ready"] is False
    assert response.json()["data"]["openai_api_key_configured"] is False
