# Cadence – NLP-Driven Language Assessment and Preparation Platform

FastAPI + PostgreSQL (Neon) backend, Next.js frontend.
Implemented so far: user accounts (FR-1), writing assessment with NLP scoring and saved
submissions (FR-3, partial), profile, and a partial dashboard. See the SRS for the full plan.

## Requirements
- **Python 3.12** (3.13 also fine; **not 3.15**, spaCy has no wheels for it yet)
- **Node.js 20+** and npm
- A **Neon** Postgres project (https://neon.tech)

## 1. Backend setup (run from `backend/`)

```bash
cd backend
python -m venv .venv                 # must be Python 3.12
source .venv/Scripts/activate        # Git Bash.  PowerShell: .venv\Scripts\Activate.ps1  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # only needed to run tests
python -m spacy download en_core_web_sm
cp .env.example .env                 # then edit .env (see below)
alembic upgrade head                 # creates all tables in Neon
uvicorn app.main:app --reload        # API on http://localhost:8000  (docs at /docs)
```

### Filling in `backend/.env`
- `DATABASE_URL`: Neon dashboard -> **Connect** -> copy the **pooled** string (host contains `-pooler`).
- `DIRECT_URL`: same screen, turn pooling **off**, copy the direct string (no `-pooler`). Used only by Alembic.
- `JWT_SECRET`: generate with
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

Check it works: open http://localhost:8000/health/db -> `{"status":"ok","database":"connected"}`

> **If your Neon database already has tables from earlier attempts**, reset it first (Neon -> SQL Editor):
> `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
> then run `alembic upgrade head`. This project ships one clean initial migration.

### Create an admin account (optional; admins cannot self-register)
```bash
python -m scripts.create_admin
```

### Run the backend tests (in-memory DB, never touches Neon)
```bash
pytest
```

## 2. Frontend setup (run from `frontend/`, in a second terminal)

```bash
cd frontend
npm install
npm run dev                          # http://localhost:3000
```
The frontend expects the API at `http://localhost:8000`. To change it, copy
`.env.local.example` to `.env.local`. For production, also add the frontend URL to
`CORS_ORIGINS` in `backend/.env` (JSON list, e.g. `["https://myapp.vercel.app"]`).

Also available: `npm run lint`, `npm run build`.

## 3. Try it
1. Open http://localhost:3000 and choose **Create free account**.
2. Go to **Writing**, write an essay, **Submit**.
3. Check the **Dashboard** and the `writing_submissions` table in Neon.

## Project layout
```
backend/
  app/
    main.py            FastAPI app, CORS, health checks
    core/              settings (.env) and security (bcrypt, JWT)
    db/                engine/session and declarative Base
    models.py          the 11 tables of SRS Table 6.1
    auth/              register, login, admin login, profile, get_current_user
    writing/           spaCy analyzer, scorer, evaluate + history endpoints
  alembic/             database migrations
  scripts/             create_admin
  tests/               pytest suite
frontend/src/
  app/                 pages: /, /login, /register, (app)/dashboard|writing|settings
  components/          shared UI
  lib/                 api client, auth context, band helpers
```

## Common problems
| Symptom | Fix |
|---|---|
| `No matching distribution found for spacy` | Your venv is Python 3.15. Recreate it with Python 3.12. |
| `ValidationError ... JWT_SECRET` on startup | Add `JWT_SECRET` (32+ chars) to `backend/.env`. |
| `Can't locate revision ...` from alembic | The Neon DB has an old `alembic_version` table. Reset the schema (see above). |
| `Can't find model 'en_core_web_sm'` | Run `python -m spacy download en_core_web_sm` inside the venv. |
| Browser shows "Cannot reach the server" | Backend not running, or the frontend URL isn't in `CORS_ORIGINS`. |
