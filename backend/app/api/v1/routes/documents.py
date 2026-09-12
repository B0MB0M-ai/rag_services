from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.rag.indexing import index_document
from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS
from app.schemas.domain import KnowledgeDocument
from app.services.documents import DocumentCategory, DocumentUploadError, store_document

router = APIRouter(prefix="/documents")


@router.get("", response_model=dict[str, object])
async def list_documents() -> dict[str, object]:
    return {
        "success": True,
        "data": KNOWLEDGE_DOCUMENTS,
        "meta": {"total": len(KNOWLEDGE_DOCUMENTS)},
    }


@router.post("", response_model=dict[str, KnowledgeDocument], status_code=status.HTTP_201_CREATED)
async def upload_document(
    category: Annotated[DocumentCategory, Form()],
    file: Annotated[UploadFile, File()],
) -> dict[str, KnowledgeDocument]:
    settings = get_settings()
    try:
        document = await store_document(
            file, category, settings.max_upload_size_mb * 1024 * 1024
        )
    except DocumentUploadError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"data": document}


@router.post("/{document_id}/index", response_model=dict[str, KnowledgeDocument])
async def reindex_document(document_id: str) -> dict[str, KnowledgeDocument]:
    document = next((item for item in KNOWLEDGE_DOCUMENTS if item.id == document_id), None)
    content = DOCUMENT_CONTENT.get(document_id)
    if document is None or content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    index_document(document, content)
    return {"data": document}
