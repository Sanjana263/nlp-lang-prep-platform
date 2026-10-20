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
_lock = threading.Lock()
_clients: dict = {}


def _client(space: str, token: str):
    with _lock:
        if space not in _clients:
            from gradio_client import Client

            _clients[space] = Client(space, token=token or None, verbose=False)
    return _clients[space]


def assess(audio_path: str, words: list[Word], space: str, token: str) -> PronunciationResult:
    if not space:
        raise SpeechServiceError("Speaking scoring isn't set up yet: add HF_SPEECH_SPACE to backend/.env.")
    from gradio_client import handle_file

    payload = json.dumps([{"text": w.text, "start": w.start, "end": w.end, "filler": w.filler} for w in words])
    try:
        raw = _client(space, token).predict(handle_file(audio_path), payload, api_name="/assess")
    except Exception as exc:  # gradio_client raises plain exceptions for queue, quota and wake-up errors
        log.exception("Pronunciation Space call failed")
        text = str(exc).lower()
        if "quota" in text:
            raise SpeechServiceError("Today's free pronunciation-check limit is used up. Your recording is saved; try scoring it again tomorrow.") from exc
        raise SpeechServiceError("The pronunciation checker is starting up or busy. Your recording is saved; try scoring it again in a minute.") from exc
    return PronunciationResult.from_dict(json.loads(raw) if isinstance(raw, str) else raw)
