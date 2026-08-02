# RAG pipeline

Phase 3 will implement ingestion and hybrid retrieval. The planned flow is: safe extraction and metadata-aware chunking; exact fault-code lookup; model/document filters; keyword and vector retrieval; weighted, deduplicated ranking; evidence threshold; structured generation; Pydantic validation; SQL part matching; backend pricing. Citations expose document title, section, page when available, and relevance score. Insufficient evidence produces escalation rather than fabrication.
