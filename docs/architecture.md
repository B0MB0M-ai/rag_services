# Architecture

Phase 1 establishes the process boundaries; this document will be expanded as components are implemented.

```mermaid
flowchart LR
  U[Service officer] --> W[Next.js web app]
  W -->|REST /api/v1| A[FastAPI]
  A --> S[Services and repositories]
  S --> P[(PostgreSQL)]
  S --> V[(pgvector chunks)]
  S -. when MOCK_AI=false .-> O[OpenAI Responses and Embeddings APIs]
```

Commercial calculations remain inside backend services using SQL facts; the AI boundary handles only cited technical interpretation and explanation.
