from pathlib import Path
from typing import Annotated, TypedDict
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS
from app.schemas.domain import KnowledgeDocument
from app.services.documents import DocumentUploadError, remove_document, store_document

web_router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


class ProductKnowledge(TypedDict):
    name: str
    images: list[KnowledgeDocument]
    manuals: list[KnowledgeDocument]


def product_knowledge() -> list[ProductKnowledge]:
    products: dict[str, ProductKnowledge] = {}
    for document in KNOWLEDGE_DOCUMENTS:
        if document.category not in {"product_image", "manual"}:
            continue
        key = document.product_name or document.id
        product = products.setdefault(
            key, {"name": document.product_name or document.filename, "images": [], "manuals": []}
        )
        documents: list[KnowledgeDocument] = product[
            "images" if document.category == "product_image" else "manuals"
        ]
        documents.append(document)
    return list(products.values())


@web_router.get("/data/documents/{document_id}")
async def document_content(document_id: str) -> Response:
    document = next((item for item in KNOWLEDGE_DOCUMENTS if item.id == document_id), None)
    content = DOCUMENT_CONTENT.get(document_id)
    if document is None or content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(
        content=content,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(document.filename, safe='')}",
            "X-Content-Type-Options": "nosniff",
        },
    )


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
            "products": product_knowledge(),
            "max_upload_size_mb": settings.max_upload_size_mb,
        },
    )


@web_router.get("/cases", response_class=HTMLResponse)
async def case_information(request: Request) -> HTMLResponse:
    """Render the service case information workspace."""
    return templates.TemplateResponse(
        request=request, name="pages/cases.html", context={"active": "cases"}
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
            raise DocumentUploadError("Enter a product name.")
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
        failed = next(
            (
                document
                for document in (image_document, manual_document)
                if document.status == "failed"
            ),
            None,
        )
        if failed is not None:
            raise DocumentUploadError(failed.indexing_error or "Document indexing failed")
        context = {
            "product_name": normalized_name,
            "products": product_knowledge(),
            "refresh_products": True,
            "error": None,
        }
    except DocumentUploadError as error:
        if stored_document_ids:
            for document_id in stored_document_ids:
                remove_document(document_id)
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
        context={
            "environment": settings.app_env,
            "mock_ai": settings.mock_ai,
            "ai_provider": "deterministic" if settings.mock_ai else "OpenAI",
            "ai_model": None if settings.mock_ai else settings.openai_response_model,
            "ai_ready": settings.mock_ai or settings.openai_api_key is not None,
        },
    )
