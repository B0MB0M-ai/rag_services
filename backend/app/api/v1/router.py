from fastapi import APIRouter

from app.api.v1.routes import assistant, catalog, documents, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(catalog.router, tags=["catalog"])
api_router.include_router(assistant.router, tags=["assistant", "estimates"])
api_router.include_router(documents.router, tags=["knowledge documents"])
