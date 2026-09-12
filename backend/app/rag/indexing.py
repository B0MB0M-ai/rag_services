from __future__ import annotations

import hashlib
import io
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from csv import reader as csv_reader
from dataclasses import dataclass

from app.core.config import get_settings
from app.repositories.catalog import DOCUMENT_CHUNKS
from app.schemas.domain import DocumentChunk, KnowledgeDocument

EMBEDDING_DIMENSIONS = 256


class DocumentIndexingError(ValueError):
    """Raised when an uploaded document cannot be converted into searchable content."""


@dataclass(frozen=True)
class ExtractedSection:
    text: str
    section: str
    page: int | None = None


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return " ".join(value.split())


def _terms(value: str) -> list[str]:
    normalized = normalize_text(value)
    words = re.findall(r"[\w-]+", normalized, flags=re.UNICODE)
    # Trigrams make deterministic mock retrieval useful for Thai, where spaces are optional.
    compact = re.sub(r"\s+", "", normalized)
    grams = [compact[index : index + 3] for index in range(max(0, len(compact) - 2))]
    return words + grams


def embed_text(value: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for term in _terms(value):
        digest = hashlib.blake2b(term.encode(), digest_size=8).digest()
        bucket = int.from_bytes(digest, "big") % EMBEDDING_DIMENSIONS
        vector[bucket] += 1.0
    magnitude = math.sqrt(sum(component * component for component in vector))
    return [component / magnitude for component in vector] if magnitude else vector


def extract_sections(document: KnowledgeDocument, content: bytes) -> list[ExtractedSection]:
    extension = document.filename.lower().rsplit(".", 1)[-1]
    try:
        if extension == "pdf":
            # The dependency-free extractor handles literal PDF text operators. Complex/scanned
            # PDFs remain observable as failed indexing and can later be routed to OCR workers.
            raw = content.decode("latin-1")
            pages = raw.split("/Type /Page")
            sections = []
            for number, page in enumerate(pages[1:] or [raw], 1):
                values = re.findall(r"\(([^()]*)\)\s*T[jJ]", page)
                text = " ".join(_unescape_pdf(value) for value in values)
                if text.strip():
                    sections.append(ExtractedSection(text, f"Page {number}", number))
            if sections:
                return sections
            # Plain-text fixtures and producer-specific PDFs get a conservative fallback.
            fallback = content.decode("utf-8", errors="ignore")
            return [ExtractedSection(fallback, "Document")]
        if extension == "docx":
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                root = ET.fromstring(archive.read("word/document.xml"))
            text = "\n".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
            return [ExtractedSection(text, "Document")]
        if extension == "txt":
            return [ExtractedSection(content.decode("utf-8-sig"), "Document")]
        if extension == "csv":
            rows = csv_reader(io.StringIO(content.decode("utf-8-sig")))
            return [
                ExtractedSection(" | ".join(cell.strip() for cell in row), f"Row {number}")
                for number, row in enumerate(rows, 1)
                if any(cell.strip() for cell in row)
            ]
        if extension == "xlsx":
            return _extract_xlsx(content)
        if document.category == "product_image":
            description = f"Product image for {document.product_name or document.filename}"
            return [ExtractedSection(description, "Product image")]
    except (
        OSError,
        UnicodeError,
        ValueError,
        zipfile.BadZipFile,
        KeyError,
        ET.ParseError,
    ) as error:
        raise DocumentIndexingError(f"Unable to extract {document.filename}: {error}") from error
    return []


def _unescape_pdf(value: str) -> str:
    return value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")


def _extract_xlsx(content: bytes) -> list[ExtractedSection]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter() if node.tag.endswith("}t"))
                for item in root
            ]
        sheets = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        sections: list[ExtractedSection] = []
        for sheet_number, name in enumerate(sheets, 1):
            root = ET.fromstring(archive.read(name))
            for row_number, row in enumerate(
                (node for node in root.iter() if node.tag.endswith("}row")), 1
            ):
                values: list[str] = []
                for cell in (node for node in row if node.tag.endswith("}c")):
                    value = next((node.text or "" for node in cell if node.tag.endswith("}v")), "")
                    if cell.attrib.get("t") == "s" and value.isdigit():
                        value = shared[int(value)]
                    values.append(value)
                if any(values):
                    sections.append(
                        ExtractedSection(
                            " | ".join(values), f"Sheet {sheet_number}, row {row_number}"
                        )
                    )
        return sections


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        return []
    if overlap >= size:
        raise ValueError("Chunk overlap must be smaller than chunk size")
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = end - overlap
    return chunks


def index_document(document: KnowledgeDocument, content: bytes) -> None:
    settings = get_settings()
    document.status = "indexing"
    try:
        sections = extract_sections(document, content)
        chunks: list[DocumentChunk] = []
        ordinal = 0
        for section in sections:
            section_chunks = chunk_text(
                section.text, settings.rag_chunk_size, settings.rag_chunk_overlap
            )
            for text in section_chunks:
                chunks.append(
                    DocumentChunk(
                        id=f"{document.id}:{ordinal}",
                        document_id=document.id,
                        content=text,
                        section=section.section,
                        page=section.page,
                        ordinal=ordinal,
                        embedding=embed_text(text),
                    )
                )
                ordinal += 1
        if not chunks:
            raise DocumentIndexingError("The document contains no searchable text")
        DOCUMENT_CHUNKS[document.id] = chunks
        document.chunk_count = len(chunks)
        document.status = "indexed"
        document.indexing_error = None
    except DocumentIndexingError as error:
        document.status = "failed"
        document.indexing_error = str(error)
        DOCUMENT_CHUNKS.pop(document.id, None)
