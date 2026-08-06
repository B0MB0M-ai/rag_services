from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.web.router import web_router

APP_DIRECTORY = Path(__file__).parent


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title="AI Service & Repair Assistant API",
        description="Portfolio demo API for evidence-based machinery service assistance.",
        version="0.1.0",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.mount(
        "/static", StaticFiles(directory=APP_DIRECTORY / "static"), name="static"
    )
    application.include_router(web_router)
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
