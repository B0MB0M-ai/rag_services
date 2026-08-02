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


class HealthResponse(BaseModel):
    success: Literal[True]
    data: HealthData


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report process health without requiring Phase 2 infrastructure."""
    settings = get_settings()
    return HealthResponse(
        success=True,
        data=HealthData(
            status="ok",
            service="ai-service-repair-backend",
            environment=settings.app_env,
            mock_ai=settings.mock_ai,
        ),
    )
