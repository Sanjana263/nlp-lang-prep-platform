"""Speech-to-text with word timings, keeping filler words.

Both modes run Whisper large-v3-turbo:
  cloud: Groq's free API (no download, no local CPU).
  local: faster-whisper on this machine's CPU (int8, about 5x faster than real time).
Whisper was trained on text with fillers removed, so a short hesitant prompt nudges it to
write "um"/"uh" down; fluency scoring depends on that.
"""
import io
import logging
import os
import re
import threading
import wave
from pathlib import Path

import numpy as np

from app.speaking.fluency import Word, mark_fillers

log = logging.getLogger(__name__)

FILLER_PROMPT = "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking. Uh, so, um, yeah."
_FILLER_RE = re.compile(r"\b(?:u+m+|u+h+|uhm|erm?|a+h+|e+h+|h+m+|mm+|mhm)\b[,.]?\s*", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Punctuated transcript without fillers, for grammar and vocabulary analysis."""
    return re.sub(r"\s+", " ", _FILLER_RE.sub("", text)).strip()


class SpeechServiceError(RuntimeError):
    """The speech service is not set up or did not answer. The message is shown to the learner."""


# ------------------------------------------------------------------ cloud (Groq)
SAMPLE_RATE = 16000


def wav_bytes(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    """16-bit mono WAV of the decoded recording.

    Sending this instead of the browser's raw webm/mp4 file means Groq never has to parse
    a container it dislikes (Chrome's streamed webm has no duration header, Safari's mp4 is
    fragmented). We already decode every upload with PyAV, so this is free.
    """
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def _field(obj, name, default=None):
    """Read a field from a pydantic model, a dict, or an object with extra attributes."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _timed_words(items) -> list[Word]:
    out = []
    for w in items or []:
        text = str(_field(w, "word", _field(w, "text", "")) or "").strip()
        start, end = _field(w, "start"), _field(w, "end")
        if text and start is not None and end is not None:
            out.append(Word(text=text, start=float(start), end=float(end)))
    return out


def _words_from_segments(segments) -> list[Word]:
    """Fallback when Groq returns text but no word list: spread each segment's words evenly
    over the segment's time span. Pauses *between* segments are kept, pauses inside are lost."""
    out = []
    for seg in segments or []:
        tokens = str(_field(seg, "text", "") or "").split()
        start, end = _field(seg, "start"), _field(seg, "end")
        if not tokens or start is None or end is None:
            continue
        step = max(float(end) - float(start), 0.01) / len(tokens)
        out += [Word(text=t, start=float(start) + i * step, end=float(start) + (i + 1) * step) for i, t in enumerate(tokens)]
    return out


def _is_prompt_echo(text: str) -> bool:
    """On near-silent audio Whisper sometimes writes the prompt itself as the transcript."""
    norm = lambda t: re.sub(r"[^a-z ]", "", t.lower()).split()
    got, prompt = norm(text), norm(FILLER_PROMPT)
    return bool(got) and len(got) <= len(prompt) + 3 and got[:6] == prompt[:6]


def _api_message(exc) -> str:
    """The reason Groq gave, e.g. 'could not process file', for logs and for the learner."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
    return str(getattr(exc, "message", "") or exc)


def transcribe_groq(
    audio_path: str, api_key: str, model: str, audio: np.ndarray | None = None
) -> tuple[list[Word], str]:
    """Returns timed words (no punctuation) and the punctuated text.

    Pass `audio` (the decoded recording) to upload a clean WAV; without it the original file
    is uploaded as it is.
    """
    api_key = (api_key or "").strip().strip("\"'")
    if not api_key:
        raise SpeechServiceError("Speaking scoring isn't set up yet: add GROQ_API_KEY to backend/.env.")
    import groq

    if audio is not None and len(audio):
        upload = ("answer.wav", wav_bytes(audio))
    else:
        upload = (Path(audio_path).name, Path(audio_path).read_bytes())

    client = groq.Groq(api_key=api_key, timeout=60.0, max_retries=1)
    try:
        result = client.audio.transcriptions.create(
            file=upload,
            model=model,
            language="en",
            prompt=FILLER_PROMPT,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            temperature=0.0,
        )
    except groq.RateLimitError as exc:
        raise SpeechServiceError("The free speech-to-text limit is used up for now. Try scoring again in a few minutes.") from exc
    except groq.AuthenticationError as exc:
        raise SpeechServiceError("The GROQ_API_KEY in backend/.env was rejected. Check the key.") from exc
    except groq.APIConnectionError as exc:
        log.exception("Groq connection failed")
        raise SpeechServiceError("Couldn't reach the speech-to-text service. Check the internet connection and score again.") from exc
    except groq.APIStatusError as exc:
        log.exception("Groq rejected the request (HTTP %s): %s", getattr(exc, "status_code", "?"), _api_message(exc))
        raise SpeechServiceError(
            f"The speech-to-text service returned an error (HTTP {getattr(exc, 'status_code', '?')}): {_api_message(exc)}"
        ) from exc

    data = result.model_dump() if hasattr(result, "model_dump") else result
    raw_text = str(_field(data, "text", "") or "")
    text = clean_text(raw_text)
    if _is_prompt_echo(raw_text):  # check before cleaning: the echo is mostly filler words
        log.warning("Groq returned the filler prompt as the transcript; treating the recording as silent")
        return [], ""

    words = _timed_words(_field(data, "words"))
    if not words:
        words = _words_from_segments(_field(data, "segments"))
        if words:
            log.warning("Groq returned no word timestamps; using segment timings instead")
        elif text:
            log.error("Groq returned text but no timings at all: %s", text[:80])
    return mark_fillers(words), text


# ------------------------------------------------------------------ local (faster-whisper)
_lock = threading.Lock()
_models: dict = {}


def _model(name: str):
    with _lock:
        if name not in _models:
            from faster_whisper import WhisperModel

            threads = max(1, (os.cpu_count() or 4) - 2)
            _models[name] = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=threads)
    return _models[name]


def transcribe_local(audio: np.ndarray, model_name: str) -> tuple[list[Word], str]:
    segments, _info = _model(model_name).transcribe(
        audio,
        language="en",
        beam_size=5,
        word_timestamps=True,
        initial_prompt=FILLER_PROMPT,
        condition_on_previous_text=False,
    )
    words = mark_fillers([Word(text=w.word.strip(), start=float(w.start), end=float(w.end)) for s in segments for w in (s.words or []) if w.word.strip()])
    return words, " ".join(w.text for w in words if not w.filler)


def transcript_text(words: list[Word]) -> str:
    """Readable transcript; fillers shown as [um] so learners can see them."""
    return " ".join(f"[{w.clean}]" if w.filler else w.text for w in words)
