from functools import lru_cache
from pathlib import Path
from typing import Literal

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

    # spaCy pipeline used by the NLP engine. Must be installed (see requirements.txt).
    SPACY_MODEL: str = "en_core_web_lg"

    # Speaking assessment (FR-5).
    # "cloud" (default): speech-to-text on Groq's free API, pronunciation on our Hugging Face
    #   ZeroGPU Space. Nothing heavy runs or downloads on this machine.
    # "local": everything runs on this machine's CPU (needs the extra packages listed in
    #   requirements.txt and ~3 GB of models).
    SPEECH_MODE: Literal["cloud", "local"] = "cloud"
    GROQ_API_KEY: str = ""
    GROQ_STT_MODEL: str = "whisper-large-v3-turbo"
    HF_TOKEN: str = ""                  # Hugging Face token; its account's daily ZeroGPU quota is used
    HF_SPEECH_SPACE: str = ""           # e.g. "your-username/cadence-speech"
    SPEECH_STT_MODEL: str = "large-v3-turbo"  # local mode: faster-whisper model
    SPEECH_PHONEME_MODEL: str = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
    UPLOAD_DIR: str = "uploads"         # relative to backend/
    SPEECH_WARMUP: bool = True          # local mode: load speech models at startup (in the background)

    # Optional: examiner-style feedback from Claude. Leave empty to use rule-based feedback only.
    ANTHROPIC_API_KEY: str = ""
    FEEDBACK_MODEL: str = "claude-opus-5-5"

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
