import numpy as np
import pytest

from app.models import SpeakingSubmission
from app.speaking import service
from app.speaking.fluency import Word, analyse, mark_fillers
from app.speaking.pronunciation import ctc_align
from app.speaking.scorer import band, round_band

FAKE_WEBM = b"\x1aE\xdf\xa3" + b"\x00" * 4000  # content is never decoded: analysis is faked below


# ---------------------------------------------------------------- fluency (unit)
def words(spec):
    """spec: list of (text, start, end)"""
    return mark_fillers([Word(t, s, e) for t, s, e in spec])


def test_fluency_counts_fillers_pauses_and_runs():
    w = words([
        ("I", 0.0, 0.2), ("like", 0.2, 0.5), ("my", 0.5, 0.7), ("city.", 0.7, 1.1),
        ("um", 1.8, 2.1),                                   # 0.7 s pause, then a filler
        ("it", 2.2, 2.4), ("is", 2.4, 2.6), ("green", 2.6, 3.0),
        ("and", 4.2, 4.4), ("and", 4.4, 4.6), ("quiet", 4.6, 5.0),  # 1.2 s pause, a repetition
    ])
    m = analyse(w)
    assert m.word_count == 10 and m.filler_count == 1
    assert m.long_pauses == 1
    assert m.repetitions == 1
    assert m.mean_length_of_run == 3.3                      # runs: 4 | 3 | 3 (filler excluded)
    assert m.words_per_minute == pytest.approx(10 / (5.0 / 60), rel=0.01)


def test_fluency_handles_only_fillers():
    m = analyse(words([("um", 0.0, 0.3), ("uh", 0.5, 0.8)]))
    assert m.word_count == 0 and m.words_per_minute == 0


# ------------------------------------------------------- alignment and bands (unit)
def test_ctc_align_assigns_frames_to_each_label():
    # 6 frames, vocab {0: blank, 1: a, 2: b}; frames say: blank a a blank b blank
    probs = np.full((6, 3), 0.05)
    for t, k in enumerate([0, 1, 1, 0, 2, 0]):
        probs[t, k] = 0.9
    frames = ctc_align(np.log(probs), [1, 2])
    assert sorted(frames[0]) == [1, 2] and frames[1] == [4]


def test_ctc_align_rejects_too_short_window():
    assert ctc_align(np.zeros((1, 3)), [1, 2]) is None


def test_band_interpolates_and_clamps():
    pts = [(60, 4), (120, 6)]
    assert band(90, pts) == 5 and band(10, pts) == 4 and band(500, pts) == 6
    assert round_band(6.24) == 6.0 and round_band(6.26) == 6.5


# ------------------------------------------------------------------- API
FAKE_RESULT = {
    "transcript": "I like my city [um] it is green",
    "bands": {"fluency": 6.0, "lexical": 6.5, "grammar": 6.0, "pronunciation": 7.0, "overall": 6.5},
    "fluency": {"words_per_minute": 118.0, "filler_count": 1},
    "mistake_patterns": [{"type": "pronunciation", "label": "/θ/ said as /t/", "count": 2, "examples": ["think"]}],
    "words": [], "feedback": ["Link your ideas."],
}


class _NoCloseSession:
    """Lets the background job use the test's session without closing it."""
    def __init__(self, s):
        self._s = s

    def __getattr__(self, name):
        return getattr(self._s, name)

    def close(self):
        pass


@pytest.fixture()
def fake_analysis(monkeypatch, db_session):
    import app.speaking.pipeline as pipeline

    monkeypatch.setattr(service, "session_factory", lambda: _NoCloseSession(db_session))
    monkeypatch.setattr(service, "load_audio", lambda path: np.zeros(16000, dtype=np.float32))
    monkeypatch.setattr(pipeline, "analyse_recording", lambda path, audio, part, q: FAKE_RESULT)
    return pipeline


def upload(client, headers, prompt_id="p1-hometown", content=FAKE_WEBM, mime="audio/webm"):
    return client.post("/speaking/submissions", headers=headers, data={"prompt_id": prompt_id},
                       files={"audio": ("answer.webm", content, mime)})


def test_prompts_require_login(client):
    assert client.get("/speaking/prompts").status_code == 401


def test_prompts_cover_all_three_parts(client, auth_headers):
    parts = {p["part"] for p in client.get("/speaking/prompts", headers=auth_headers).json()}
    assert parts == {1, 2, 3}


def test_submit_scores_in_background_and_saves_result(client, auth_headers, db_session, fake_analysis):
    r = upload(client, auth_headers)
    assert r.status_code == 202
    sid = r.json()["speaking_id"]

    detail = client.get(f"/speaking/submissions/{sid}", headers=auth_headers).json()
    assert detail["status"] == "completed"
    assert detail["overall_band"] == 6.5 and detail["pronunciation_score"] == 7.0
    assert detail["filler_word_count"] == 1 and detail["pace_score"] == 118.0
    assert detail["mistake_patterns_json"][0]["label"] == "/θ/ said as /t/"
    row = db_session.get(SpeakingSubmission, sid)
    assert row.part_number == 1 and row.prompt_text.startswith("Where is your hometown")


def test_failed_analysis_keeps_recording_and_can_retry(client, auth_headers, fake_analysis, monkeypatch):
    def boom(path, audio, part, q):
        raise RuntimeError("model crashed")

    monkeypatch.setattr(fake_analysis, "analyse_recording", boom)
    sid = upload(client, auth_headers).json()["speaking_id"]
    detail = client.get(f"/speaking/submissions/{sid}", headers=auth_headers).json()
    assert detail["status"] == "failed" and "recording is saved" in detail["error_message"]
    assert client.get(f"/speaking/submissions/{sid}/audio", headers=auth_headers).status_code == 200

    monkeypatch.setattr(fake_analysis, "analyse_recording", lambda path, audio, part, q: FAKE_RESULT)
    assert client.post(f"/speaking/submissions/{sid}/retry", headers=auth_headers).status_code == 202
    assert client.get(f"/speaking/submissions/{sid}", headers=auth_headers).json()["status"] == "completed"


def test_rejects_non_audio_and_unknown_question(client, auth_headers, fake_analysis):
    assert upload(client, auth_headers, mime="text/plain").status_code == 415
    assert upload(client, auth_headers, prompt_id="nope").status_code == 422
    assert upload(client, auth_headers, content=b"tiny").status_code == 422


def test_cannot_see_other_users_recordings(client, auth_headers, fake_analysis):
    sid = upload(client, auth_headers).json()["speaking_id"]
    other = client.post("/auth/register", json={"full_name": "B", "email": "b@example.com",
                        "password": "secret123", "target_exam": "TOEFL"}).json()["access_token"]
    h = {"Authorization": f"Bearer {other}"}
    assert client.get(f"/speaking/submissions/{sid}", headers=h).status_code == 404
    assert client.get(f"/speaking/submissions/{sid}/audio", headers=h).status_code == 404
    assert client.get("/speaking/submissions", headers=h).json() == []


# ------------------------------------------------------------ optional examiner
def test_examiner_is_skipped_without_api_key():
    from app.speaking import examiner

    assert examiner.review("q", 1, "I like my city", {}) is None


def test_examiner_failure_falls_back_to_rules(monkeypatch):
    import anthropic

    from app.core.config import get_settings
    from app.speaking import examiner

    monkeypatch.setattr(get_settings(), "ANTHROPIC_API_KEY", "sk-test")

    class Boom:
        def __init__(self, *a, **k):
            raise anthropic.APIConnectionError(request=None)

    monkeypatch.setattr(anthropic, "Anthropic", Boom)
    assert examiner.review("q", 1, "I like my city", {}) is None


# --------------------------------------------------------- cloud mode (Groq + Space)
def test_clean_text_strips_fillers_but_keeps_words():
    from app.speaking.stt import clean_text

    assert clean_text("Um, I think, uh, my hummus is umm good. Mm, yes.") == "I think, my hummus is good. yes."


def test_groq_transcription_is_parsed_into_timed_words(monkeypatch, tmp_path):
    import groq

    from app.speaking import stt

    class FakeResult:
        def model_dump(self):
            return {"text": "Um, I like it.", "words": [
                {"word": "Um", "start": 0.0, "end": 0.3}, {"word": "I", "start": 0.5, "end": 0.6},
                {"word": "like", "start": 0.6, "end": 0.9}, {"word": "it", "start": 0.9, "end": 1.1}]}

    sent = {}

    class FakeGroq:
        def __init__(self, **kw):
            self.audio = type("A", (), {"transcriptions": type("T", (), {"create": lambda _s, **k: sent.update(k) or FakeResult()})()})()

    monkeypatch.setattr(groq, "Groq", FakeGroq)
    f = tmp_path / "a.webm"
    f.write_bytes(b"x" * 10)
    words, text = stt.transcribe_groq(str(f), "gsk_test", "whisper-large-v3-turbo")
    assert [w.text for w in words] == ["Um", "I", "like", "it"] and words[0].filler
    assert text == "I like it."
    assert sent["timestamp_granularities"] == ["word"] and sent["prompt"] == stt.FILLER_PROMPT


def test_missing_cloud_keys_give_a_clear_message(tmp_path):
    from app.speaking import pronunciation_remote, stt

    with pytest.raises(stt.SpeechServiceError, match="GROQ_API_KEY"):
        stt.transcribe_groq(str(tmp_path / "a.webm"), "", "whisper-large-v3-turbo")
    with pytest.raises(stt.SpeechServiceError, match="HF_SPEECH_SPACE"):
        pronunciation_remote.assess(str(tmp_path / "a.webm"), [], "", "")


def test_space_result_round_trips():
    from app.speaking.pronunciation import PhoneResult, PronunciationResult, WordPronunciation

    r = PronunciationResult(0.9, [WordPronunciation(2, "think", 0.75, [PhoneResult("θ", "t", False)])], {"θ→t": ["think"]})
    back = PronunciationResult.from_dict(r.to_dict())
    assert back == r and back.scored


def test_cloud_pipeline_uses_groq_and_space(monkeypatch):
    from app.core.config import get_settings
    from app.speaking import pipeline, pronunciation_remote, stt
    from app.speaking.pronunciation import PronunciationResult

    monkeypatch.setattr(get_settings(), "SPEECH_MODE", "cloud")
    words = mark_fillers([Word(t, i * 0.4, i * 0.4 + 0.3) for i, t in enumerate("I really like living in my city".split())])
    monkeypatch.setattr(stt, "transcribe_groq", lambda path, key, model: (words, "I really like living in my city."))
    monkeypatch.setattr(pronunciation_remote, "assess", lambda path, w, space, token: PronunciationResult(0.9, []))
    r = pipeline.analyse_recording("a.webm", np.zeros(16000, dtype=np.float32), 1, "Where is your hometown?")
    assert r["transcript"].startswith("I really") and 1 <= r["bands"]["overall"] <= 9
