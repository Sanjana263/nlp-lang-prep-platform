"""Pronunciation scoring on our Hugging Face ZeroGPU Space (cloud mode).

The Space (speech-space/ in this repo) runs the same code as app/speaking/pronunciation.py
on a free shared GPU. Each call uses a few seconds of the HF_TOKEN account's daily ZeroGPU
quota (5 GPU-minutes a day on a free account).
"""
import json
import logging
import threading

from app.speaking.fluency import Word
from app.speaking.pronunciation import PronunciationResult
from app.speaking.stt import SpeechServiceError

log = logging.getLogger(__name__)
CALL_TIMEOUT = 120  # seconds to wait for the Space, so a stuck call can't block every later answer
_lock = threading.Lock()
_clients: dict = {}


def _client(space: str, token: str):
    with _lock:
        if space not in _clients:
            from gradio_client import Client

            # A sleeping Space can take a minute or two to answer its first request.
            _clients[space] = Client(space, token=token or None, verbose=False, httpx_kwargs={"timeout": 60})
    return _clients[space]


def _predict(space: str, token: str, audio_path: str, payload: str):
    """One call to the Space that gives up after CALL_TIMEOUT seconds instead of waiting forever."""
    from gradio_client import handle_file

    job = _client(space, token).submit(handle_file(audio_path), payload, api_name="/assess")
    try:
        return job.result(timeout=CALL_TIMEOUT)
    except TimeoutError:
        job.cancel()
        raise


def assess(audio_path: str, words: list[Word], space: str, token: str) -> PronunciationResult:
    if not space:
        raise SpeechServiceError("Speaking scoring isn't set up yet: add HF_SPEECH_SPACE to backend/.env.")
    payload = json.dumps([{"text": w.text, "start": w.start, "end": w.end, "filler": w.filler} for w in words])
    try:
        try:
            raw = _predict(space, token, audio_path, payload)
        except Exception as first:
            # The first GPU call after the Space starts or wakes often runs out of time while
            # ZeroGPU sets the GPU up ("GPU task aborted"); the next call is quick. Retry once.
            if "aborted" not in str(first).lower():
                raise
            log.warning("Pronunciation Space call aborted (cold GPU); retrying once")
            raw = _predict(space, token, audio_path, payload)
    except Exception as exc:  # gradio_client raises plain exceptions for queue, quota and wake-up errors
        log.exception("Pronunciation Space call failed")
        text = str(exc).lower()
        if isinstance(exc, TimeoutError):
            raise SpeechServiceError(
                "The pronunciation checker took too long (it may be waking up). Your recording is saved; try scoring it again in a minute."
            ) from exc
        if "repository not found" in text or "404" in text:
            raise SpeechServiceError(
                f"The pronunciation checker '{space}' doesn't exist yet. Deploy it with "
                "scripts.deploy_speech_space (see README), or fix HF_SPEECH_SPACE in backend/.env."
            ) from exc
        if "quota" in text:
            raise SpeechServiceError("Today's free pronunciation-check limit is used up. Your recording is saved; try scoring it again tomorrow.") from exc
        raise SpeechServiceError("The pronunciation checker is starting up or busy. Your recording is saved; try scoring it again in a minute.") from exc
    return PronunciationResult.from_dict(json.loads(raw) if isinstance(raw, str) else raw)
