from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env  (this file lives in backend/app/core/)
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _normalize(url: str) -> str:
    """Neon gives 'postgresql://...'; SQLAlchemy needs the driver named."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # Neon POOLED connection string (host contains "-pooler") -> used by the app
    DATABASE_URL: str
    # Neon DIRECT connection string (no "-pooler") -> used by Alembic migrations.
    # Optional: falls back to DATABASE_URL.
    DIRECT_URL: str | None = None

    # Auth (FR-1, NFR-2). Generate with:  python -c "import secrets; print(secrets.token_urlsafe(48))"
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # NFR-2.5: session expires after this long

    # spaCy pipeline used by the NLP engine. Must be installed (see pyproject.toml).
    SPACY_MODEL: str = "en_core_web_lg"

    # Origins allowed to call the API from a browser (the Next.js dev server by default)
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("DATABASE_URL", "DIRECT_URL")
    @classmethod
    def _fix_scheme(cls, v):
        return _normalize(v) if v else v

    @property
    def migration_url(self) -> str:
        return self.DIRECT_URL or self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()
