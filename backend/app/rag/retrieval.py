from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.rag.indexing import embed_text, normalize_text
from app.repositories.catalog import DOCUMENT_CHUNKS, KNOWLEDGE_DOCUMENTS
from app.schemas.domain import DocumentChunk, KnowledgeDocument


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    document: KnowledgeDocument
    score: float
    keyword_score: float
    vector_score: float
    exact_score: float


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _keyword_score(query: str, content: str) -> float:
    query_terms = set(re.findall(r"[\w-]+", normalize_text(query)))
    content_terms = set(re.findall(r"[\w-]+", normalize_text(content)))
    if not query_terms:
        return 0.0
    return len(query_terms & content_terms) / len(query_terms)


def _exact_fault_score(query: str, content: str) -> float:
    fault_codes = re.findall(r"\b[a-z]+(?:-[a-z0-9]+)+\b", normalize_text(query))
    normalized_content = normalize_text(content)
    return 1.0 if any(code in normalized_content for code in fault_codes) else 0.0


def retrieve(query: str, product_hint: str | None = None) -> list[RetrievalResult]:
    settings = get_settings()
    query_embedding = embed_text(query)
    documents = {document.id: document for document in KNOWLEDGE_DOCUMENTS}
    candidates: list[RetrievalResult] = []
    normalized_hint = normalize_text(product_hint) if product_hint else None
    for document_id, chunks in DOCUMENT_CHUNKS.items():
        document = documents.get(document_id)
        if not document or document.status != "indexed":
            continue
        if normalized_hint and normalized_hint not in normalize_text(document.product_name or ""):
            continue
        for chunk in chunks:
            keyword = _keyword_score(query, chunk.content)
            vector = max(0.0, _cosine(query_embedding, chunk.embedding))
            exact = _exact_fault_score(query, chunk.content)
            metadata = (
                0.1
                if document.product_name
                and normalize_text(document.product_name) in normalize_text(query)
                else 0.0
            )
            score = min(1.0, keyword * 0.45 + vector * 0.3 + exact * 0.15 + metadata)
            candidates.append(RetrievalResult(chunk, document, score, keyword, vector, exact))
    candidates.sort(key=lambda item: (-item.score, item.chunk.document_id, item.chunk.ordinal))
    # A chunk is unique by ID, so this final slice is the explainable, deduplicated merge.
    return candidates[: settings.rag_final_context_count]
