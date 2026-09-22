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

For the deployed Vercel frontend, Render sets the session cookie to `SameSite=None; Secure`, allowing the authenticated cookie to travel with credentialed cross-site API requests. Local development remains `SameSite=Lax` over HTTP.

## Design decisions and limitations

AI output is validated against Pydantic schemas. If no provider is configured, deterministic extraction still identifies URLs/emails/phones and reports unavailable AI enrichment instead of fabricating facts. OCR uses PyMuPDF/PyPDF text extraction and Tesseract when installed. Q&A uses lexical retrieval locally; set up pgvector embeddings in PostgreSQL for semantic retrieval in production. Background notifications need a scheduler/worker (Celery, RQ, or platform cron) to deliver reminders.

See [docs/API.md](docs/API.md) for endpoint details.

### Image OCR

The deployment image installs Tesseract for the backend. JPG, JPEG, and PNG uploads are processed through `pytesseract`; successful OCR text follows the same `create_notice` extraction/task pipeline as PDF and pasted-text notices. The application never hardcodes a machine-specific path. `TESSERACT_CMD` is only needed when running the backend outside the supplied Docker image. When OCR is unavailable or the image contains no readable text, the API returns a specific error and preserves no fabricated extraction.


### Google Sign-In

Google Sign-In uses Google Identity Services in the browser and verifies every returned ID token on the FastAPI server. It creates no frontend secret and continues to issue the existing `noticelens_session` HttpOnly cookie.

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project and configure the OAuth consent screen.
2. Go to **APIs & Services → Credentials → Create credentials → OAuth client ID**, choose **Web application**, and create the client.
3. Add authorized JavaScript origins: `http://localhost:5173` and `https://notiq-wine.vercel.app`. Add any custom production domain as another origin.
4. Copy the Web client ID (ends in `.apps.googleusercontent.com`). No client secret belongs in this application.
5. Set `GOOGLE_CLIENT_ID` to that exact value for the backend locally and in Render. In Vercel, set `VITE_GOOGLE_CLIENT_ID` to the same value, then redeploy both services.

The backend checks the token audience, issuer, signature and verified email before locating or creating an account. Existing accounts retain their password login; accounts first created with Google receive a cryptographically random, unknown password hash.
### Document upload handling

- Supported: PDF, DOCX, PNG, JPG and JPEG.
- Password-protected or encrypted PDFs receive a specific message.
- Damaged/non-PDF files renamed as `.pdf` receive a specific message.
- Valid PDFs without extractable text receive a specific scanned/image-only PDF message; upload clear page images for OCR or paste the text.
- Empty DOCX files receive a specific no-readable-paragraphs message; malformed/corrupt DOCX files receive a specific document-read message.
- Image OCR errors and unavailable OCR receive their existing specific messages. Unexpected file-copy, parser and storage failures are logged with ERROR-level tracebacks and return a safe generic processing message.