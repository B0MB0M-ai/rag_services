from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS
from app.services.documents import DocumentUploadError, store_document

web_router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@web_router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Render the application landing page."""
    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={"active": "dashboard", "document_count": len(KNOWLEDGE_DOCUMENTS)},
    )


@web_router.get("/assistant", response_class=HTMLResponse)
async def assistant(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="pages/assistant.html", context={"active": "assistant"}
    )


@web_router.get("/data", response_class=HTMLResponse)
async def data_upload(request: Request) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="pages/data_upload.html",
        context={
            "active": "data",
            "documents": KNOWLEDGE_DOCUMENTS,
            "max_upload_size_mb": settings.max_upload_size_mb,
        },
    )


@web_router.post("/data/upload", response_class=HTMLResponse)
async def data_upload_submit(
    request: Request,
    product_name: Annotated[str, Form(min_length=1, max_length=200)],
    product_image: Annotated[UploadFile, File()],
    manual: Annotated[UploadFile, File()],
) -> HTMLResponse:
    settings = get_settings()
    stored_document_ids: list[str] = []
    try:
        normalized_name = product_name.strip()
        if not normalized_name:
            raise DocumentUploadError("กรุณาระบุชื่อสินค้า")
        image_document = await store_document(
            product_image,
            "product_image",
            settings.max_upload_size_mb * 1024 * 1024,
            normalized_name,
        )
        stored_document_ids.append(image_document.id)
        manual_document = await store_document(
            manual,
            "manual",
            settings.max_upload_size_mb * 1024 * 1024,
            normalized_name,
        )
        stored_document_ids.append(manual_document.id)
        context = {
            "product_name": normalized_name,
            "documents": [image_document, manual_document],
            "error": None,
        }
    except DocumentUploadError as error:
        if stored_document_ids:
            KNOWLEDGE_DOCUMENTS[:] = [
                document
                for document in KNOWLEDGE_DOCUMENTS
                if document.id not in stored_document_ids
            ]
            for document_id in stored_document_ids:
                DOCUMENT_CONTENT.pop(document_id, None)
        context = {"documents": [], "error": str(error)}
    return templates.TemplateResponse(
        request=request, name="partials/upload_result.html", context=context
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
