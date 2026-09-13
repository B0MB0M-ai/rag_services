from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter()


class HealthData(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    mock_ai: bool
    ai_provider: Literal["openai", "deterministic"]
    ai_model: str | None
    ai_ready: bool
    openai_api_key_configured: bool


class HealthResponse(BaseModel):
    success: Literal[True]
    data: HealthData


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report process health and the effective, non-secret AI configuration."""
    settings = get_settings()
    api_key_configured = settings.openai_api_key is not None
    return HealthResponse(
        success=True,
        data=HealthData(
            status="ok",
            service="ai-service-repair-backend",
            environment=settings.app_env,
            mock_ai=settings.mock_ai,
            ai_provider="deterministic" if settings.mock_ai else "openai",
            ai_model=None if settings.mock_ai else settings.openai_response_model,
            ai_ready=settings.mock_ai or api_key_configured,
            openai_api_key_configured=api_key_configured,
        ),
    )
