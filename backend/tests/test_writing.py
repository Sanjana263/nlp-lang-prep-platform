from sqlalchemy import select

from app.models import WritingSubmission

ESSAY = ("Although some people believe that university education should be free, others argue that "
         "students must contribute because the government has limited funds. In my opinion, a balanced "
         "system, which helps poor students, is the best solution for society.")


def test_evaluate_requires_login(client):
    assert client.post("/writing/evaluate", json={"essay": ESSAY}).status_code == 401


def test_evaluate_saves_submission(client, auth_headers, db_session):
    r = client.post("/writing/evaluate", headers=auth_headers,
                    json={"essay": ESSAY, "task_type": "task2", "prompt_text": "Free university?"})
    assert r.status_code == 200
    body = r.json()
    sub = db_session.scalar(select(WritingSubmission))
    assert sub.writing_id == body["submission_id"]
    assert sub.status == "completed"
    assert sub.grammar_score == body["bands"]["grammar"]
    assert sub.task_response_score == body["bands"]["task_response"]
    assert sub.submitted_text == ESSAY


def test_history_only_shows_own_submissions(client, auth_headers):
    client.post("/writing/evaluate", headers=auth_headers, json={"essay": ESSAY})
    other = client.post("/auth/register", json={**{"full_name": "B", "password": "secret123",
                        "target_exam": "TOEFL"}, "email": "b@example.com"}).json()["access_token"]
    mine = client.get("/writing/submissions", headers=auth_headers).json()
    theirs = client.get("/writing/submissions", headers={"Authorization": f"Bearer {other}"}).json()
    assert len(mine) == 1 and theirs == []


def test_analysis_failure_keeps_submission(client, auth_headers, db_session, monkeypatch):
    import app.writing.router as wr
    monkeypatch.setattr(wr, "analyze_essay", lambda t: (_ for _ in ()).throw(RuntimeError("boom")))
    c = client.__class__(client.app, raise_server_exceptions=False)
    r = c.post("/writing/evaluate", headers=auth_headers, json={"essay": ESSAY})
    assert r.status_code == 500
    sub = db_session.scalar(select(WritingSubmission))
    assert sub is not None and sub.status == "failed"                                   # NFR-3.2
