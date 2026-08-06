# Architecture

Phase 1 establishes the process boundaries; this document will be expanded as components are implemented.

```mermaid
flowchart LR
  U[Service officer] --> A[FastAPI web application]
  A -->|renders| W[Jinja2 + HTMX + Alpine.js]
  W -->|HTML requests| A
  A --> S[Services and repositories]
  S --> P[(PostgreSQL)]
  S --> V[(pgvector chunks)]
  S -. when MOCK_AI=false .-> O[OpenAI Responses and Embeddings APIs]
```

Commercial calculations remain inside backend services using SQL facts; the AI boundary handles only cited technical interpretation and explanation.
