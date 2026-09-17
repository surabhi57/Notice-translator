# NOTICE LENS

NOTICE LENS is a full-stack college-notice assistant. It accepts text, PDFs, and images; preserves the source notice; extracts structured facts; creates tasks/deadlines; and answers grounded questions with citations.

## Architecture

- `frontend/`: React, TypeScript, Vite, Tailwind, React Router, TanStack Query
- `backend/`: FastAPI, SQLAlchemy, Pydantic, JWT, replaceable AI/OCR services
- `docs/`: API and deployment notes

## Quick start

1. Copy `backend/.env.example` to `backend/.env` and set `SECRET_KEY`.
2. Start Postgres (optional for local development); SQLite is the default fallback.
3. `cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt && uvicorn app.main:app --reload`
4. `cd frontend && npm install && npm run dev`

Open `http://localhost:5173`. The API docs are at `http://localhost:8000/docs`.

## Deployment

Set `DATABASE_URL=postgresql+psycopg://...`, `SECRET_KEY`, `CORS_ORIGINS`, and either `OPENAI_API_KEY` (with `AI_PROVIDER=openai`) or `GEMINI_API_KEY` (with `AI_PROVIDER=gemini`). Use object storage for `UPLOAD_DIR` in production. Run behind HTTPS and a reverse proxy; apply a rate limiter such as Redis at the edge.

## Design decisions and limitations

AI output is validated against Pydantic schemas. If no provider is configured, deterministic extraction still identifies URLs/emails/phones and reports unavailable AI enrichment instead of fabricating facts. OCR uses PyMuPDF/PyPDF text extraction and Tesseract when installed. Q&A uses lexical retrieval locally; set up pgvector embeddings in PostgreSQL for semantic retrieval in production. Background notifications need a scheduler/worker (Celery, RQ, or platform cron) to deliver reminders.

See [docs/API.md](docs/API.md) for endpoint details.
