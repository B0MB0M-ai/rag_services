# Detailed implementation plan

## Principles and boundaries

This portfolio demo favors transparent, testable components. RAG supplies evidence-based technical guidance and candidate part identifiers. PostgreSQL supplies all current commercial facts. Backend services calculate money using `Decimal` or integer satang. The OpenAI provider explains validated results but is never a price authority. If retrieval evidence is below the configured threshold, the response contains no invented procedure or part number and directs the officer to a technician.

## Target architecture

1. **Next.js web client** — App Router layouts, role-aware navigation, typed API client, forms validated with Zod/React Hook Form, reusable shadcn/ui components, charts, and PDF download.
2. **FastAPI application** — versioned routers and dependencies delegate to services and repositories; centralized errors produce consistent envelopes; structured logs capture correlation IDs without secrets.
3. **PostgreSQL + pgvector** — normalized operational data and immutable/revisioned pricing in relational tables; embeddings only on document chunks, with full-text indexes alongside vector indexes.
4. **Document pipeline** — validated uploads, format-specific extraction, preview, semantic chunking, metadata enrichment, embedding, and observable indexing states.
5. **RAG orchestration** — normalization, exact fault lookup, metadata filters, keyword/vector retrieval, explainable merge, Pydantic-validated generation, SQL part matching, then deterministic pricing.
6. **Provider boundary** — interchangeable deterministic mock and official OpenAI Responses API implementations; model names and retrieval controls are environment-driven.

## Phase 1 — foundation (this change)

- Establish repository guidance, configuration examples, Docker Compose, ignore rules, and monorepo directories.
- Scaffold a typed FastAPI application with versioned health routing and a test.
- Scaffold a strict Next.js App Router application with Tailwind, accessible status page, lint/type/test configuration, and a test.
- Document local and container startup plus explicit phase limitations.
- Acceptance: backend unit test and lint pass; frontend unit test, lint, typecheck, and production build pass; Compose config validates.

## Phase 2 — database, migrations, and machine API

- Configure async SQLAlchemy sessions, pgvector extension, Alembic, timestamp/soft-delete/revision mixins, UUID conventions, and repository dependencies.
- Model all specified business entities and constraints. Store monetary amounts as integer satang (preferred) with currency, and percentage/rate inputs as exact numerics.
- Generate the initial migration from models; add appropriate B-tree, full-text, uniqueness, and vector indexes.
- Create deterministic synthetic seed factories for 6 models, 20+ parts, 20+ cases, 15+ codes, 10+ service records, and pricing/warranty rules.
- Add health readiness and machine list/detail/fault-code endpoints with envelope schemas, pagination, errors, and API tests.
- Add JWT login, seeded demo roles/users, RBAC dependencies, CORS configuration, structured logging, and rate-limit abstraction.

## Phase 3 — ingestion and transparent retrieval

- Implement safe upload validation (extension, MIME, size, filename normalization, isolated storage) and extraction adapters for PDF, DOCX, CSV, and XLSX.
- Add text preview, deterministic metadata-aware chunking, indexing status/error tracking, and embedding batching.
- Implement Thai/English normalization, exact error-code retrieval, metadata constraints, PostgreSQL full-text/keyword search, pgvector cosine search, deduplication, and explainable weighted scoring.
- Expose every score component and source coordinate. Add three clearly synthetic guides under `backend/sample_data/documents/`.
- Implement deterministic mock embeddings/retrieval and document endpoints. Unit test chunking and score merge/ranking.

## Phase 4 — diagnosis, pricing, estimates, and PDF

- Define strict diagnosis/citation schemas and provider interface. Implement mock diagnoses and official OpenAI Responses structured output with validation/retry boundaries.
- Enforce the evidence threshold and mandatory preliminary-assessment warning; persist conversations, messages, retrieval/usage logs, diagnoses, and feedback.
- Match proposed part identifiers through repositories; reject unknown pricing. Build an exact pricing engine for quantities, labor hours, fees, travel, discount, VAT, warranty, and rounding.
- Add chat, conversation, diagnosis, estimates, parts/pricing, feedback, and professional bilingual preliminary-PDF endpoints.
- Test price cases, mock chat, estimate lifecycle, insufficient evidence, provider failures, and PDF generation.

## Phase 5 — complete enterprise UI

- Build the navy/cyan responsive shell and all specified navigation destinations with loading, empty, validation, and friendly error states.
- Build the three-column assistant (case context, chat, diagnosis/cost), follow-ups, evidence badges, checklists, safety callouts, parts editor, and technician warning.
- Build estimate editor/PDF workflow, machine/fault/manual views, knowledge upload/preview/indexing, parts/pricing configuration, dashboard charts, history, feedback, and settings.
- Add typed API/domain layers and accessible components. Unit test the repair calculator presentation.

## Phase 6 — integration, automation, and documentation

- Add login-to-estimate Playwright flow for HP-500 oil leakage in mock mode.
- Add GitHub Actions jobs for backend and frontend lint, tests, type checks, build, and E2E with service containers.
- Exercise startup, migrations, seed/index scripts, CORS, upload errors, provider outage paths, responsive layouts, and quotation download.
- Complete architecture, schema/ER, RAG/scoring, API, demo script, screenshots, operational notes, limitations, and future roadmap.

## Planned package boundaries

Backend code is separated into `api`, `core`, `db`, `models`, `schemas`, `repositories`, `services`, `rag`, `document_processing`, `prompts`, and `utils`. Frontend code is separated into App Router routes, shared `components`, domain `features`, `hooks`, API/utilities in `lib`, shared `types`, and tests.

## Phase gates

At every phase: review secrets and business boundaries; format; lint; typecheck; run relevant unit/API/E2E tests; validate Compose; report changed files, exact commands, and limitations. A later phase cannot silently weaken evidence, pricing, citation, upload, authentication, or privacy controls.
