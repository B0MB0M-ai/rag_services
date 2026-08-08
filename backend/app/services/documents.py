from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import UploadFile

from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS
from app.schemas.domain import KnowledgeDocument

DocumentCategory = Literal["machine", "product_image", "manual"]

ALLOWED_EXTENSIONS: dict[DocumentCategory, set[str]] = {
    "machine": {".csv", ".xlsx"},
    "product_image": {".jpg", ".jpeg", ".png", ".webp"},
    "manual": {".pdf", ".docx", ".txt"},
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
        raise DocumentUploadError(f"ไฟล์ประเภทนี้ไม่รองรับ (รองรับ {expected})")

    content = await upload.read(max_size_bytes + 1)
    await upload.close()
    if not content:
        raise DocumentUploadError("ไฟล์ว่างเปล่า กรุณาเลือกไฟล์ที่มีข้อมูล")
    if len(content) > max_size_bytes:
        raise DocumentUploadError(
            f"ไฟล์มีขนาดเกิน {max_size_bytes // (1024 * 1024)} MB"
        )

    document = KnowledgeDocument(
        id=str(uuid4()),
        filename=filename,
        category=category,
        product_name=product_name,
        size_bytes=len(content),
        content_type=upload.content_type or "application/octet-stream",
        uploaded_at=datetime.now(UTC),
    )
    KNOWLEDGE_DOCUMENTS.insert(0, document)
    DOCUMENT_CONTENT[document.id] = content
    return document
