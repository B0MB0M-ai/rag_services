# AI Service & Repair Assistant

**ระบบผู้ช่วยฝ่ายบริการและประเมินค่าซ่อมเครื่องจักรด้วย RAG**

An internal portfolio-demo application for industrial machinery service officers. The finished product will combine cited maintenance knowledge with authoritative SQL pricing to create preliminary diagnoses and repair estimates in Thai or English.

> **Phase status:** Integrated portfolio demo. The application includes a polished dashboard,
> service-assistant workflow, deterministic cited mock diagnosis, catalog APIs, and exact
> server-side estimate calculation. PostgreSQL persistence, production authentication, document
> extraction, and PDF rendering remain deployment extensions described below.

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
Browser -> FastAPI :8000 -> PostgreSQL 16 + pgvector
           |    |              (business data + chunks)
           |    `-> OpenAI Responses/Embeddings (optional)
           `-> Jinja2 templates + HTMX/Alpine.js
```

FastAPI serves both `GET /api/v1/health` and the responsive web interface. The data-ingestion
workspace at `GET /data` accepts machine spreadsheets and technical documents, while
`POST /api/v1/documents` exposes the same upload capability to API clients. Jinja2 renders full
pages and HTML fragments, HTMX handles server interactions, and Alpine.js provides small
client-side behaviors.

## Technology stack

- **Web UI:** Server-rendered Jinja2 templates, HTMX, Alpine.js, and repository-owned CSS
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Uvicorn
- **Data/RAG:** PostgreSQL, pgvector, custom hybrid retrieval, official OpenAI Python SDK
- **Documents/PDF:** PyMuPDF, python-docx, pandas/openpyxl, WeasyPrint (added with their feature phases)
- **Quality:** Ruff, Pytest, Playwright, GitHub Actions (expanded by phase)

## Quick start with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:8000>. API documentation is at <http://localhost:8000/docs>, and health is at <http://localhost:8000/api/v1/health>.

## Run without Docker

Prerequisite: Python 3.12.

For a one-command setup and start, run this from the repository root:

```bash
./run.sh
```

The script creates `.env` and `.venv` when needed, installs the backend development
dependencies, and starts Uvicorn with auto-reload. Any additional arguments are passed to
Uvicorn, for example `./run.sh --port 8080`. You can also set `HOST` or `PORT`, such as
`PORT=8080 ./run.sh`.

If startup reports that port 8000 is already in use, another application (often an earlier
Uvicorn process) is already listening there. On macOS, find it with `lsof -nP -iTCP:8000
-sTCP:LISTEN`, then stop that process with `kill <PID>`. Alternatively, leave it running and
start this application on a different port with `./run.sh --port 8080`. The script checks the
selected address before starting and prints these alternatives when a conflict is detected.

To perform the same setup manually:

```bash
cp .env.example .env
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The same Uvicorn process serves the web interface and versioned API; no frontend development server is required.

PostgreSQL is not used by the Phase 1 health skeleton. From Phase 2 onward, run the Compose database or provide a compatible `DATABASE_URL`.

## Environment variables

Copy `.env.example` rather than committing `.env`. Important values are `DATABASE_URL`, `MOCK_AI`, server-only `OPENAI_API_KEY`, model names, CORS origins, upload limits, and retrieval tuning values.

## Data, seeding, and indexing

A new workspace starts empty: it does not preload machines, parts, service cases, prices, or
knowledge documents. Customer data must be explicitly imported after the corresponding persistence
and ingestion workflows are configured. Automated tests create their own isolated fixtures; no
proprietary manual is included.

## Testing and checks

```bash
cd backend && ruff check . && pytest
```

Phase 1 contains API, server-rendered page, and HTMX fragment tests. Playwright coverage arrives during integration.

## Demo accounts

Phase 2 will seed one demo-only administrator and one service officer. No credentials exist in Phase 1.

## Screenshots

<!-- Replace with product screenshots after the application workflows are implemented. -->

_Placeholder: dashboard, three-column Service Assistant, and preliminary quotation screens._

## Current limitations

- Catalog and uploaded-document records currently use an in-process repository; uploaded files
  are available for the future extraction/indexing stage but reset when the process restarts.
  Production deployments should replace this with the planned SQLAlchemy and object-storage
  repositories.
- Authentication, live document ingestion, OpenAI mode, and downloadable PDF rendering are not
  enabled in this portfolio build.
- Docker images are development-oriented and are not hardened production artifacts.

## Future improvements

After the six MVP phases: SSO, background ingestion workers, OCR, reranking evaluation, multilingual observability, approval workflows, inventory integration, and production deployment hardening.
