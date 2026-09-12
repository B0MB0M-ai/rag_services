# RAG pipeline

The application now provides a deterministic, end-to-end local RAG pipeline. Uploads are validated,
extracted by format (PDF, DOCX, TXT, CSV, and XLSX), split into overlapping metadata-aware chunks,
embedded with a stable hash-based embedding, and indexed immediately. Images contribute searchable
product metadata; OCR is intentionally left to a future worker.

At query time, normalized Thai/English text is compared using keyword overlap and cosine vector
similarity. Product metadata can constrain retrieval, the two scores are merged and deduplicated,
and only chunks above `RAG_MIN_EVIDENCE_SCORE` may reach answer generation. With the default
`MOCK_AI=false`, all selected chunks and their relevance scores are sent to the configured model,
which is instructed to reconcile the evidence into diagnosis, prioritized checks, confirmation
signals, and a focused follow-up question rather than reproduce the excerpts. With `MOCK_AI=true`,
answers quote retrieved evidence deterministically for explicit offline/test use.
Both modes expose the document, section, page when available, and relevance score.
Insufficient evidence produces escalation rather than fabrication. Candidate part identifiers are
never inferred by the local generator; pricing remains an independent backend concern.

Indexing state is visible as `indexing`, `indexed`, or `failed`, including an error message and chunk
count. `POST /api/v1/documents/{document_id}/index` retries indexing. The current repository is
process-local so the index is deterministic and fully testable without external services. A
production deployment should replace the repository and hash embeddings with PostgreSQL/pgvector,
object storage, background workers, and the configured embedding provider without changing the
retrieval or diagnosis boundaries.
