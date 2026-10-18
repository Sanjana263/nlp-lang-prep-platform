from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

engine = create_engine(
    get_settings().DATABASE_URL,
    pool_pre_ping=True,   # Neon suspends idle compute; this revives dead connections
    pool_recycle=300,     # drop connections older than 5 min
    pool_size=5,
    max_overflow=5,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency: one DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
