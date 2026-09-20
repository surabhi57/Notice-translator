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

Set `DATABASE_URL=postgresql+psycopg://...`, `SECRET_KEY`, `CORS_ORIGINS`, and either `OPENAI_API_KEY` (with `AI_PROVIDER=openai`) or `GEMINI_API_KEY` (with `AI_PROVIDER=gemini`). `CORS_ORIGINS` defaults to `http://localhost:5173,https://notiq-wine.vercel.app`; preserve both values when setting it in Render. Use object storage for `UPLOAD_DIR` in production. Run behind HTTPS and a reverse proxy; apply a rate limiter such as Redis at the edge.

Build and run the backend with its supplied production image:

```bash
docker build -t noticelens-api ./backend
docker run --env-file ./backend/.env -p 8000:8000 noticelens-api
```

The backend Docker image installs Tesseract and English, Hindi, and Kannada OCR language data. OCR is therefore a deployment dependency, never a student/user dependency. Set `SESSION_COOKIE_SECURE=true` behind HTTPS. `TESSERACT_CMD` is optional in the Docker image because `tesseract` is already on `PATH`; it remains available for non-container development environments.

The repository excludes local environments, package caches, uploaded runtime files, SQLite databases, and generated frontend bundles. The backend build context also has its own `.dockerignore`, keeping deployment images dependent only on source code and declared Python packages.
### Render

Deploy the supplied `render.yaml` as a Render Blueprint. It uses the Docker runtime with `backend/Dockerfile`; Render automatically builds the image, installs the Linux Tesseract packages, and runs the image `CMD`. That command starts FastAPI on Render's assigned `PORT`. The Blueprint sets `TESSERACT_CMD=/usr/bin/tesseract`; configure the synced `CORS_ORIGINS` value in Render before deployment. Local Windows setups continue to use the optional `TESSERACT_CMD` from `backend/.env`.

The Blueprint provisions `notiq-postgres` and wires its private connection string to `DATABASE_URL`. Production must use this persistent Postgres database; container-local SQLite is only for local development and is not suitable for retaining registered accounts across Render deploys.

## Design decisions and limitations

AI output is validated against Pydantic schemas. If no provider is configured, deterministic extraction still identifies URLs/emails/phones and reports unavailable AI enrichment instead of fabricating facts. OCR uses PyMuPDF/PyPDF text extraction and Tesseract when installed. Q&A uses lexical retrieval locally; set up pgvector embeddings in PostgreSQL for semantic retrieval in production. Background notifications need a scheduler/worker (Celery, RQ, or platform cron) to deliver reminders.

See [docs/API.md](docs/API.md) for endpoint details.

### Image OCR

The deployment image installs Tesseract for the backend. JPG, JPEG, and PNG uploads are processed through `pytesseract`; successful OCR text follows the same `create_notice` extraction/task pipeline as PDF and pasted-text notices. The application never hardcodes a machine-specific path. `TESSERACT_CMD` is only needed when running the backend outside the supplied Docker image. When OCR is unavailable or the image contains no readable text, the API returns a specific error and preserves no fabricated extraction.

