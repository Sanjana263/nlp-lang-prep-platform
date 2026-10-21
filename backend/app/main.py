import logging
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.router import router as auth_router, users_router
from app.core.config import get_settings
from app.db.session import get_db
from app.speaking.router import router as speaking_router
from app.writing.router import router as writing_router


def _fail_orphaned_jobs() -> None:
    """Background jobs live in this process, so a restart (including uvicorn --reload after any
    code change) silently kills them and leaves their rows "pending" forever. Mark them failed
    so the learner can press "Score it again". Assumes one server process, as in `npm run dev`."""
    try:
        from sqlalchemy import update

        from app.db.session import SessionLocal
        from app.models import SpeakingSubmission

        with SessionLocal() as db:
            n = db.execute(
                update(SpeakingSubmission)
                .where(SpeakingSubmission.status.in_(("pending", "processing")))
                .values(status="failed", error_message="Scoring was interrupted when the server restarted. Your recording is saved; press Score it again.")
            ).rowcount
            db.commit()
        if n:
            log.warning("Marked %s interrupted speaking submission(s) as failed so they can be retried", n)
    except Exception:
        log.exception("Could not clean up interrupted speaking submissions")


@asynccontextmanager
async def lifespan(_: FastAPI):
    _fail_orphaned_jobs()
    settings = get_settings()
    if settings.SPEECH_MODE == "local" and settings.SPEECH_WARMUP:
        from app.speaking.service import warm_up

        threading.Thread(
            target=warm_up, args=(settings.SPEECH_STT_MODEL, settings.SPEECH_PHONEME_MODEL), daemon=True
        ).start()
    yield


log = logging.getLogger(__name__)
app = FastAPI(title="Cadence API", lifespan=lifespan)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(writing_router)
app.include_router(speaking_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Confirms the API can actually reach Postgres (Neon)."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {type(exc).__name__}")
    return {"status": "ok", "database": "connected"}
