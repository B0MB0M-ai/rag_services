# Repository Agent Guide

## Scope and structure

This guide applies to the entire repository. The monorepo contains a Next.js frontend in `frontend/`, a FastAPI service in `backend/`, infrastructure at the root, and design documentation in `docs/`.

## Coding standards

- Python targets 3.12. Use type hints, Pydantic v2, async endpoints where appropriate, Ruff formatting/linting, and separate routers, services, repositories, schemas, and models.
- TypeScript must remain strict. Do not use `any` unless the reason is documented next to the use. Prefer accessible, reusable React components and App Router server components by default.
- Keep secrets server-side, use structured logging, and never log credentials or API keys.
- Store money as integer satang or `Decimal`; never use binary floating point for business calculations.
- Never put prices in prompts as the source of truth. Prices come from PostgreSQL and calculations belong in backend code.
- Do not make LangChain a required dependency.

## Database and migrations

- Use SQLAlchemy 2 models and Alembic-generated revisions.
- Never modify generated migrations manually after creation. Correct the models and generate a new migration instead.
- Use pgvector only for document chunks and semantic retrieval.

## Commands

- Full stack: `docker compose up --build`
- Backend dev: `cd backend && uvicorn app.main:app --reload`
- Backend checks: `cd backend && ruff check . && pytest`
- Frontend dev: `cd frontend && npm run dev`
- Frontend checks: `cd frontend && npm run lint && npm run typecheck && npm test`
- End-to-end (when implemented): `cd frontend && npm run test:e2e`

## Testing requirements

- Always run relevant formatting, linting, type checks, and tests before completing a task.
- Add regression coverage with business logic and API changes.
- Pricing tests must cover VAT, discounts, quantities, zero travel fees, decimal labor hours, and rounding.
- Mock external AI calls in automated tests.
