import os

# Set BEFORE the app is imported. Env vars beat .env, so tests never touch Neon.
os.environ["DATABASE_URL"] = "sqlite:///./unused_test.db"   # engine is never used; get_db is overridden
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-123456"
os.environ["SPEECH_WARMUP"] = "false"   # no model loading in tests
os.environ["ANTHROPIC_API_KEY"] = ""     # never call the LLM from tests
os.environ["UPLOAD_DIR"] = os.path.join(os.path.dirname(__file__), ".uploads")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, import_models
from app.db.session import get_db
from app.main import app


@compiles(JSONB, "sqlite")          # let SQLite stand in for Postgres in tests
def _jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


import_models()


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


REG = {"full_name": "Ananya Rao", "email": "Ananya@Example.com", "password": "secret123", "target_exam": "IELTS"}


@pytest.fixture()
def auth_headers(client):
    r = client.post("/auth/register", json=REG)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
