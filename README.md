# Cadence – NLP-Driven Language Assessment and Preparation Platform

FastAPI + PostgreSQL (Neon) backend, Next.js frontend.
Implemented so far: user accounts (FR-1), writing assessment with NLP scoring and saved
submissions (FR-3, partial), profile, and a partial dashboard. See the SRS for the full plan.

## Requirements (install once)
- **Node.js 20+** and npm
- **Python 3.12 or 3.13** installed (it can sit next to a newer Python; setup finds it
  automatically via `py -3.12` / `python3.12`). Not 3.14+: spaCy has no wheels for it yet.
- A **Neon** Postgres project (https://neon.tech)

## 1. Setup (once, from the repo root)

```bash
npm run setup
```
This creates `backend/.venv` on Python 3.12/3.13, `pip install`s `backend/requirements.txt`
(including the spaCy `en_core_web_lg` model), installs the frontend,
creates `backend/.env` with a generated `JWT_SECRET`, and runs the migrations. The
first run downloads about 500 MB, mostly the spaCy model.

On the first run it stops and asks you to fill in two values in `backend/.env`:
- `DATABASE_URL`: Neon dashboard -> **Connect** -> copy the **pooled** string (host contains `-pooler`).
- `DIRECT_URL`: same screen, turn pooling **off**, copy the direct string (no `-pooler`). Used only by Alembic.

## 2. Run (every day)

```bash
npm run dev        # API on http://localhost:8000 (docs at /docs) + web on http://localhost:3000
```
It applies any new migrations first, then starts both servers in one terminal.
After pulling changes that touch `requirements.txt` or `package.json`, run `npm run setup` again.

Check the API: http://localhost:8000/health/db -> `{"status":"ok","database":"connected"}`

### Other commands (repo root)
| Command | What it does |
|---|---|
| `npm test` | Backend tests (in-memory DB, never touches Neon) |
| `npm run lint` | Frontend lint |
| `npm run migrate` | Apply database migrations |
| `npm run create-admin` | Create an admin account (admins cannot self-register) |

For any other backend command, activate the venv inside `backend/` first
(`source .venv/Scripts/activate` in Git Bash, `.venv\Scripts\Activate.ps1` in PowerShell,
`source .venv/bin/activate` on macOS/Linux), e.g. `alembic revision --autogenerate -m "..."`.
To add a package, add it with a pinned version to `backend/requirements.txt` and run `npm run setup`.

> **If your Neon database already has tables from earlier attempts**, reset it first (Neon -> SQL Editor):
> `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
> then run `npm run migrate`. This project ships one clean initial migration.

The frontend expects the API at `http://localhost:8000`. To change it, copy
`frontend/.env.local.example` to `frontend/.env.local`. For production, also add the frontend URL to
`CORS_ORIGINS` in `backend/.env` (JSON list, e.g. `["https://myapp.vercel.app"]`).

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
| `No matching distribution found for spacy` | The venv is on Python 3.14+. Run `npm run setup`; it rebuilds the venv on 3.12/3.13. |
| `ValidationError ... JWT_SECRET` on startup | Add `JWT_SECRET` (32+ chars) to `backend/.env`. |
| `Can't locate revision ...` from alembic | The Neon DB has an old `alembic_version` table. Reset the schema (see above). |
| `Can't find model 'en_core_web_lg'` | Run `npm run setup` (the model is listed in `requirements.txt`). |
| `Python 3.12 or 3.13 is required` | Install Python 3.12 from python.org, then re-run `npm run setup`. |
| Browser shows "Cannot reach the server" | Backend not running, or the frontend URL isn't in `CORS_ORIGINS`. |
