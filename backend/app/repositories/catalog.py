from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import RLock
from typing import Any

from app.core.config import get_settings
from app.schemas.domain import DocumentChunk, KnowledgeDocument, Machine, Part, ServiceCase

logger = logging.getLogger(__name__)
_storage_lock = RLock()

# A new workspace must not imply that customer-owned equipment or commercial data
# already exists. These collections are populated only through an explicit import
# once persistence and ingestion are configured.
MACHINES: list[Machine] = []
PARTS: list[Part] = []
KNOWLEDGE_DOCUMENTS: list[KnowledgeDocument] = []
# Process-local storage keeps uploaded content available to a later extraction/indexing step.
DOCUMENT_CONTENT: dict[str, bytes] = {}
DOCUMENT_CHUNKS: dict[str, list[DocumentChunk]] = {}
SERVICE_CASES: list[ServiceCase] = []


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def _write_json(path: Path, payload: object) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    _atomic_write(path, content)


def persist_documents() -> None:
    """Persist uploaded files, metadata, and their searchable RAG chunks."""
    with _storage_lock:
        data_directory = get_settings().app_data_dir
        blob_directory = data_directory / "documents"
        blob_directory.mkdir(parents=True, exist_ok=True)
        document_ids = {document.id for document in KNOWLEDGE_DOCUMENTS}
        for document_id in document_ids:
            content = DOCUMENT_CONTENT.get(document_id)
            if content is not None:
                _atomic_write(blob_directory / document_id, content)
        for blob in blob_directory.iterdir():
            if blob.is_file() and not blob.name.startswith(".") and blob.name not in document_ids:
                blob.unlink()
        _write_json(
            data_directory / "knowledge.json",
            {
                "version": 1,
                "documents": [document.model_dump(mode="json") for document in KNOWLEDGE_DOCUMENTS],
                "chunks": {
                    document_id: [chunk.model_dump(mode="json") for chunk in chunks]
                    for document_id, chunks in DOCUMENT_CHUNKS.items()
                    if document_id in document_ids
                },
            },
        )


def persist_service_cases() -> None:
    with _storage_lock:
        _write_json(
            get_settings().app_data_dir / "service_cases.json",
            {
                "version": 1,
                "cases": [service_case.model_dump(mode="json") for service_case in SERVICE_CASES],
            },
        )


def save_service_case(service_case: ServiceCase) -> None:
    """Append and persist one case atomically; safe to call from a background thread."""
    with _storage_lock:
        SERVICE_CASES.insert(0, service_case)
        _write_json(
            get_settings().app_data_dir / "service_cases.json",
            {
                "version": 1,
                "cases": [item.model_dump(mode="json") for item in SERVICE_CASES],
            },
        )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def load_persistent_state() -> None:
    """Restore durable application state when a new server process starts."""
    with _storage_lock:
        data_directory = get_settings().app_data_dir
        knowledge_path = data_directory / "knowledge.json"
        case_path = data_directory / "service_cases.json"

        KNOWLEDGE_DOCUMENTS.clear()
        DOCUMENT_CONTENT.clear()
        DOCUMENT_CHUNKS.clear()
        SERVICE_CASES.clear()

        if knowledge_path.exists():
            try:
                payload = _read_json(knowledge_path)
                chunks = payload.get("chunks", {})
                for item in payload.get("documents", []):
                    document = KnowledgeDocument.model_validate(item)
                    blob_path = data_directory / "documents" / document.id
                    if not blob_path.is_file():
                        logger.warning(
                            "Skipping document %s because its file is missing", document.id
                        )
                        continue
                    KNOWLEDGE_DOCUMENTS.append(document)
                    DOCUMENT_CONTENT[document.id] = blob_path.read_bytes()
                    DOCUMENT_CHUNKS[document.id] = [
                        DocumentChunk.model_validate(chunk) for chunk in chunks.get(document.id, [])
                    ]
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                logger.exception("Unable to restore persisted knowledge data")

        if case_path.exists():
            try:
                payload = _read_json(case_path)
                SERVICE_CASES.extend(
                    ServiceCase.model_validate(item) for item in payload.get("cases", [])
                )
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                logger.exception("Unable to restore persisted service cases")


def get_part(part_id: str) -> Part | None:
    return next((part for part in PARTS if part.id == part_id), None)
