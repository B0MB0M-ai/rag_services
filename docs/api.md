# API

All endpoints use `/api/v1`, with interactive OpenAPI at `/docs`. `POST /api/v1/documents` validates,
stores, extracts, chunks, and indexes an uploaded knowledge document; `GET /api/v1/documents` lists
its status and `POST /api/v1/documents/{document_id}/index` retries indexing. `POST /api/v1/chat`
retrieves indexed evidence and returns a typed answer with confidence, citations, candidate part IDs,
and the mandatory preliminary-assessment warning. Catalog and deterministic estimate endpoints use
consistent typed response envelopes.
