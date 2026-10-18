from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.router import router as auth_router, users_router
from app.core.config import get_settings
from app.db.session import get_db
from app.writing.router import router as writing_router

app = FastAPI(title="Cadence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(writing_router)


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
