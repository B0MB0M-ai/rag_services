from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import UploadFile

from app.rag.indexing import index_document
from app.repositories.catalog import DOCUMENT_CHUNKS, DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS
from app.schemas.domain import KnowledgeDocument

DocumentCategory = Literal["machine", "product_image", "manual"]

ALLOWED_EXTENSIONS: dict[DocumentCategory, set[str]] = {
    "machine": {".csv", ".xlsx"},
    "product_image": {".jpg", ".jpeg", ".png", ".webp"},
    "manual": {".pdf", ".docx", ".txt"},
}
ALLOWED_CONTENT_TYPES: dict[str, set[str]] = {
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".txt": {"text/plain"},
}


class DocumentUploadError(ValueError):
    """Raised when a knowledge document is not safe to accept."""


async def store_document(
    upload: UploadFile,
    category: DocumentCategory,
    max_size_bytes: int,
    product_name: str | None = None,
) -> KnowledgeDocument:
    filename = Path(upload.filename or "").name
    extension = Path(filename).suffix.lower()
    if not filename or extension not in ALLOWED_EXTENSIONS[category]:
        expected = ", ".join(sorted(ALLOWED_EXTENSIONS[category]))
        raise DocumentUploadError(f"Unsupported file type (supported: {expected})")
    content_type = (upload.content_type or "application/octet-stream").lower()
    if content_type not in ALLOWED_CONTENT_TYPES[extension]:
        raise DocumentUploadError(
            f"File content type {content_type!r} does not match the {extension} extension"
        )

    content = await upload.read(max_size_bytes + 1)
    await upload.close()
    if not content:
        raise DocumentUploadError("The file is empty. Select a file that contains data.")
    if len(content) > max_size_bytes:
        raise DocumentUploadError(
            f"The file exceeds the {max_size_bytes // (1024 * 1024)} MB limit"
        )

    document = KnowledgeDocument(
        id=str(uuid4()),
        filename=filename,
        category=category,
        product_name=product_name,
        size_bytes=len(content),
        content_type=content_type,
        uploaded_at=datetime.now(UTC),
    )
    KNOWLEDGE_DOCUMENTS.insert(0, document)
    DOCUMENT_CONTENT[document.id] = content
    index_document(document, content)
    return document


def remove_document(document_id: str) -> None:
    """Remove a document and all derived data as one logical operation."""
    KNOWLEDGE_DOCUMENTS[:] = [item for item in KNOWLEDGE_DOCUMENTS if item.id != document_id]
    DOCUMENT_CONTENT.pop(document_id, None)
    DOCUMENT_CHUNKS.pop(document_id, None)
