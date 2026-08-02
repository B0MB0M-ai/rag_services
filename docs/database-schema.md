# Database schema

The normalized schema and Mermaid ER diagram will be generated from the Phase 2 SQLAlchemy design. Planned entity groups are identity/RBAC, machinery and customers, service workflow, pricing and estimates, knowledge documents/chunks, and conversation/retrieval/usage feedback logs. PostgreSQL holds business data; pgvector is restricted to chunk embeddings.
