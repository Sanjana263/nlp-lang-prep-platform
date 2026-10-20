"""Speech-to-text with word timings, keeping filler words.

Both modes run Whisper large-v3-turbo:
  cloud: Groq's free API (no download, no local CPU).
  local: faster-whisper on this machine's CPU (int8, about 5x faster than real time).
Whisper was trained on text with fillers removed, so a short hesitant prompt nudges it to
write "um"/"uh" down; fluency scoring depends on that.
"""
import os
import re
import threading
from pathlib import Path

import numpy as np

from app.speaking.fluency import Word, mark_fillers

FILLER_PROMPT = "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking. Uh, so, um, yeah."
_FILLER_RE = re.compile(r"\b(?:u+m+|u+h+|uhm|erm?|a+h+|e+h+|h+m+|mm+|mhm)\b[,.]?\s*", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Punctuated transcript without fillers, for grammar and vocabulary analysis."""
    return re.sub(r"\s+", " ", _FILLER_RE.sub("", text)).strip()


class SpeechServiceError(RuntimeError):
    """The speech service is not set up or did not answer. The message is shown to the learner."""


# ------------------------------------------------------------------ cloud (Groq)
def transcribe_groq(audio_path: str, api_key: str, model: str) -> tuple[list[Word], str]:
    """Returns timed words (no punctuation) and the punctuated text."""
    if not api_key:
        raise SpeechServiceError("Speaking scoring isn't set up yet: add GROQ_API_KEY to backend/.env.")
    import groq

    client = groq.Groq(api_key=api_key, timeout=120.0, max_retries=2)
    try:
        result = client.audio.transcriptions.create(
            file=(Path(audio_path).name, Path(audio_path).read_bytes()),
            model=model,
            language="en",
            prompt=FILLER_PROMPT,
            response_format="verbose_json",
            timestamp_granularities=["word"],
            temperature=0.0,
        )
    except groq.RateLimitError as exc:
        raise SpeechServiceError("The free speech-to-text limit is used up for now. Try scoring again in a few minutes.") from exc
    except groq.AuthenticationError as exc:
        raise SpeechServiceError("The GROQ_API_KEY in backend/.env was rejected. Check the key.") from exc
    except (groq.APIConnectionError, groq.APIStatusError) as exc:
        raise SpeechServiceError("The speech-to-text service didn't respond. Try scoring again.") from exc

    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    words = [Word(text=str(w["word"]).strip(), start=float(w["start"]), end=float(w["end"])) for w in data.get("words") or []]
    return mark_fillers([w for w in words if w.text]), clean_text(str(data.get("text") or ""))


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
