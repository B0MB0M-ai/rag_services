from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

web_router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@web_router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Render the application landing page."""
    return templates.TemplateResponse(
        request=request, name="pages/home.html", context={"active": "dashboard"}
    )


@web_router.get("/assistant", response_class=HTMLResponse)
async def assistant(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="pages/assistant.html", context={"active": "assistant"}
    )


@web_router.get("/partials/health-status", response_class=HTMLResponse)
async def health_status(request: Request) -> HTMLResponse:
    """Render a small HTMX health-status fragment."""
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="partials/health_status.html",
        context={"environment": settings.app_env, "mock_ai": settings.mock_ai},
    )
