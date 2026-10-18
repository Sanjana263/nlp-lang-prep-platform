from sqlalchemy import select

from app.models import User
from tests.conftest import REG


def test_register_ok_and_password_hashed(client, db_session):
    r = client.post("/auth/register", json=REG)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "ananya@example.com"      # normalised
    assert body["user"]["role"] == "student"
    assert "password" not in str(body).lower().replace("password_hash", "")
    u = db_session.scalar(select(User))
    assert u.password_hash != REG["password"] and u.password_hash.startswith("$2")  # FR-1.3
    assert u.created_at is not None                                                    # FR-1.7


def test_register_duplicate_email_rejected(client):
    client.post("/auth/register", json=REG)
    r = client.post("/auth/register", json={**REG, "email": "ananya@EXAMPLE.com"})
    assert r.status_code == 409                                                        # FR-1.2


def test_register_validation(client):
    assert client.post("/auth/register", json={**REG, "target_exam": "GRE"}).status_code == 422
    assert client.post("/auth/register", json={**REG, "password": "short"}).status_code == 422
    assert client.post("/auth/register", json={**REG, "email": "nope"}).status_code == 422


def test_login_ok(client):
    client.post("/auth/register", json=REG)
    r = client.post("/auth/login", json={"email": "ANANYA@example.com", "password": "secret123"})
    assert r.status_code == 200 and r.json()["access_token"]                            # FR-1.4


def test_login_failures_are_indistinguishable(client):
    client.post("/auth/register", json=REG)
    wrong_pw = client.post("/auth/login", json={"email": REG["email"], "password": "wrongwrong"})
    no_user = client.post("/auth/login", json={"email": "ghost@example.com", "password": "secret123"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()                                            # FR-1.5


def test_me_requires_token(client):
    assert client.get("/users/me").status_code == 401                                   # NFR-2.1
    assert client.get("/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_profile_view_and_update(client, auth_headers):
    assert client.get("/users/me", headers=auth_headers).json()["full_name"] == "Ananya Rao"
    r = client.put("/users/me", headers=auth_headers, json={"target_exam": "PTE"})
    assert r.status_code == 200 and r.json()["target_exam"] == "PTE"                    # FR-1.6
    assert r.json()["full_name"] == "Ananya Rao"


def test_admin_login_separate(client, db_session):
    from app.core.security import hash_password
    db_session.add(User(full_name="Root", email="admin@x.com", password_hash=hash_password("adminpass1"),
                        target_exam="IELTS", role="admin"))
    db_session.commit()
    creds = {"email": "admin@x.com", "password": "adminpass1"}
    assert client.post("/auth/admin/login", json=creds).status_code == 200              # FR-1.8
    assert client.post("/auth/login", json=creds).status_code == 401                    # not via student login
    client.post("/auth/register", json=REG)
    assert client.post("/auth/admin/login", json={"email": REG["email"], "password": "secret123"}).status_code == 401


def test_expired_token_rejected(client, monkeypatch):
    from app.core import security
    monkeypatch.setattr(security.get_settings(), "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    r = client.post("/auth/register", json=REG)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/users/me", headers=h).status_code == 401                        # NFR-2.5


def test_cors_allows_frontend_origin(client):
    r = client.options("/auth/login", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    bad = client.options("/auth/login", headers={"Origin": "http://evil.example",
                                                 "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
