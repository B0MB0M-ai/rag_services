# AI Service & Repair Assistant

**ระบบผู้ช่วยฝ่ายบริการและประเมินค่าซ่อมเครื่องจักรด้วย RAG**

An internal portfolio-demo application for industrial machinery service officers. The finished product will combine cited maintenance knowledge with authoritative SQL pricing to create preliminary diagnoses and repair estimates in Thai or English.

> **Phase status:** Phase 1 foundation only. The current UI and API are intentionally minimal; RAG, authentication, business entities, quotations, and demo data are planned for later phases.

## Business problem and guardrails

Service teams need fast, traceable guidance across manuals, repair cases, fault codes, parts, and pricing. The assistant will retrieve evidence for technical guidance while PostgreSQL remains the sole source for prices, rates, VAT, fees, and warranties. The language model will never invent or calculate monetary values. Low-evidence questions will be escalated to a qualified technician, and every diagnosis will be marked as preliminary.

## Planned capabilities

- Thai/English service conversation with machine and fault-code context
- Transparent hybrid retrieval with document, section, page, and score citations
- Decimal-safe repair estimates and editable preliminary quotation PDFs
- Machine, knowledge-base, parts/pricing, history, feedback, and dashboard workflows
- Deterministic `MOCK_AI=true` demo mode with no external AI cost

See the phased scope and acceptance checks in [the implementation plan](docs/implementation-plan.md).

## Architecture

```text
Browser / Next.js :3000 -> FastAPI /api/v1 :8000 -> PostgreSQL 16 + pgvector
                                      |            (business data + chunks)
                                      `-> OpenAI Responses/Embeddings (optional)
```

The Phase 1 backend exposes `GET /api/v1/health`; the frontend provides a responsive project-status landing page. Detailed component and data-flow diagrams will be completed in Phase 2.

## Technology stack

- **Frontend:** Next.js App Router, strict TypeScript, Tailwind CSS; shadcn/ui, Lucide, Recharts, React Hook Form, Zod planned
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Uvicorn
- **Data/RAG:** PostgreSQL, pgvector, custom hybrid retrieval, official OpenAI Python SDK
- **Documents/PDF:** PyMuPDF, python-docx, pandas/openpyxl, WeasyPrint (added with their feature phases)
- **Quality:** Ruff, Pytest, ESLint, Vitest, Playwright, GitHub Actions (expanded by phase)

## Quick start with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:3000>. API documentation is at <http://localhost:8000/docs>, and health is at <http://localhost:8000/api/v1/health>.

## Run without Docker

Prerequisites: Node.js 20+, npm, and Python 3.12.

```bash
cp .env.example .env
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

PostgreSQL is not used by the Phase 1 health skeleton. From Phase 2 onward, run the Compose database or provide a compatible `DATABASE_URL`.

## Environment variables

Copy `.env.example` rather than committing `.env`. Important values are `DATABASE_URL`, `MOCK_AI`, server-only `OPENAI_API_KEY`, model names, CORS origins, upload limits, and retrieval tuning values. No secret may use a `NEXT_PUBLIC_` prefix.

## Demo data, seeding, and indexing

Synthetic documents will live in `backend/sample_data/documents/`. Phase 2 will add database seeding; Phase 3 will add document indexing. No proprietary manual will be included.

## Testing and checks

```bash
cd backend && ruff check . && pytest
cd frontend && npm run lint && npm run typecheck && npm test
```

Phase 1 contains backend health tests and a frontend landing-page unit test. Playwright coverage arrives during integration.

## Demo accounts

Phase 2 will seed one demo-only administrator and one service officer. No credentials exist in Phase 1.

## Screenshots

<!-- Replace with product screenshots after the application workflows are implemented. -->

_Placeholder: dashboard, three-column Service Assistant, and preliminary quotation screens._

## Current limitations

- No database models, migrations, seed records, authentication, RAG, estimates, PDF output, or feature UI yet.
- The Phase 1 landing page is a scaffold rather than the final enterprise interface.
- Docker images are development-oriented and are not hardened production artifacts.

## Future improvements

After the six MVP phases: SSO, background ingestion workers, OCR, reranking evaluation, multilingual observability, approval workflows, inventory integration, and production deployment hardening.
