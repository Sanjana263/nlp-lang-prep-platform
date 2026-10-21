# Cadence – NLP-Driven Language Assessment and Preparation Platform

FastAPI + PostgreSQL (Neon) backend, Next.js frontend.
Implemented so far: user accounts (FR-1), writing assessment with NLP scoring (FR-3, partial),
speaking assessment with speech-to-text and pronunciation scoring (FR-5), profile, and a
partial dashboard. See the SRS for the full plan.

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
first run downloads about 500 MB, mostly the spaCy model. Speech models run in the cloud,
so nothing else is downloaded (see "Speaking setup" below).

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
3. Go to **Speaking**, pick a question, allow the microphone, record an answer and submit it.
   Scoring takes 20–60 seconds on a laptop CPU.
4. Check the **Dashboard** and the `writing_submissions` / `speaking_submissions` tables in Neon.

## Speaking setup (free, once per person)
The speech models run in the cloud at no cost, so laptops only upload the recording.

1. **Groq key** (speech-to-text): sign in at https://console.groq.com, open **API Keys**,
   **Create API Key**, and put it in `backend/.env` as `GROQ_API_KEY`.
2. **Hugging Face token** (pronunciation): at https://huggingface.co/settings/tokens choose
   **Create new token**, type **Write**, and put it in `backend/.env` as `HF_TOKEN`.
3. **The pronunciation Space** (one teammate, once): set `HF_SPEECH_SPACE=your-username/cadence-speech`
   in `backend/.env`, then from `backend/` run
   ```bash
   .venv/Scripts/python -m scripts.deploy_speech_space   # macOS/Linux: .venv/bin/python -m ...
   ```
   It creates the Space on free ZeroGPU hardware and builds in a few minutes
   (needs a Hugging Face account that is at least 30 days old with a verified email).
   Everyone else just sets `HF_SPEECH_SPACE` to that same name, with their own `HF_TOKEN`.

Free limits: Groq allows about 8 hours of audio a day; ZeroGPU gives each Hugging Face
account 5 GPU-minutes a day, roughly 60-100 answers. The first answer after the Space has
been idle can take a few minutes while it wakes up.

To run everything offline on your own machine instead, set `SPEECH_MODE=local` and install the
extra packages listed at the bottom of `backend/requirements.txt` (~1.5 GB, plus ~3 GB of models
on first use, and heavy CPU use).

## How speaking is scored
Recordings are sent to Groq and to our Hugging Face Space for scoring.

| Step | Model / method | Gives |
|---|---|---|
| Speech-to-text | Whisper **large-v3-turbo** on Groq, prompted to keep fillers | transcript, word timings, "um"/"uh" |
| Fluency | word timings | speech rate, words between pauses, pauses/min, long pauses, fillers, repetitions |
| Pronunciation | **wav2vec2** phoneme recogniser (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`) on our ZeroGPU Space + espeak-ng expected phonemes, CTC forced alignment (GOP) | per-sound accuracy, mispronounced sounds such as /θ/ said as /t/ |
| Vocabulary, grammar | spaCy `en_core_web_lg` + `wordfreq` on the transcript | lexical diversity (MATTR), less-common words, clause complexity |
| Bands | `app/speaking/scorer.py` | the four IELTS Speaking criteria and an overall band |

**Validation.** On a first sample of 55 expert-rated learner recordings from
[speechocean762](https://www.openslr.org/101/), our pronunciation score ranks learners in the same
order as the experts with Spearman ρ ≈ 0.4, and the band mapping is fitted to those ratings.
Run `python -m scripts.calibrate_speaking` (in `backend/`, local mode) for the full calibration.

US and UK pronunciations both count as correct, and accent features that don't hurt
intelligibility (for example Indian-English retroflex t/d) are not marked down.

**Optional AI examiner.** Set `ANTHROPIC_API_KEY` in `backend/.env` and Claude also reviews the
transcript: it re-scores vocabulary and grammar (it can spot actual errors) and adds corrections.
It never scores fluency or pronunciation, because it can't hear the audio. Without a key
everything still works with the built-in feedback.

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
    speaking/          audio decoding, speech-to-text (Groq or local), fluency, pronunciation
                       (Space or local), scorer, optional LLM examiner, background job, endpoints
  alembic/             database migrations
  scripts/             create_admin, deploy_speech_space, calibrate_speaking
speech-space/          Hugging Face ZeroGPU Space for pronunciation (deployed by the script above)
  tests/               pytest suite
frontend/src/
  app/                 pages: /, /login, /register, (app)/dashboard|writing|speaking|settings
  components/          shared UI; speaking/ holds the recorder and result screens
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
| "Microphone access is blocked" | Allow the microphone for localhost in the browser's site settings. Recording needs `http://localhost` or https. |
| Speaking answer has no transcript, or you aren't sure which stage fails | Run `npm run check-speech -- backend/uploads/speaking/<user id>/<file>.webm`. It tests the key, decoding, Groq and the Space one by one and prints the exact error. |
| Speaking result says "pronunciation check wasn't available" | The transcript and the other three bands are fine; only the Hugging Face Space failed (not deployed, asleep or out of daily quota). Fix `HF_SPEECH_SPACE` / `HF_TOKEN`, or ignore it. |
| Speaking answer fails: "isn't set up yet" | Add `GROQ_API_KEY`, `HF_TOKEN` and `HF_SPEECH_SPACE` to `backend/.env` (see Speaking setup), restart `npm run dev`. |
| Speaking answer fails: "starting up or busy" | The Space was asleep or still building. Open it on huggingface.co to check, then **Score it again**. |
| "Today's free pronunciation-check limit is used up" | Your Hugging Face account's 5 daily ZeroGPU minutes are spent; it resets 24 hours after first use. |
| Browser shows "Cannot reach the server" | Backend not running, or the frontend URL isn't in `CORS_ORIGINS`. |
