"""Full speaking analysis for one recording: STT -> fluency -> pronunciation -> text -> bands."""
import logging
import time
from dataclasses import asdict

import numpy as np

from app.core.config import get_settings
from app.speaking import examiner, pronunciation_remote, scorer, stt
from app.speaking.fluency import analyse as analyse_fluency
from app.speaking.pronunciation import PronunciationResult
from app.speaking.stt import SpeechServiceError

log = logging.getLogger(__name__)


class NoSpeechError(ValueError):
    """The recording had no recognisable speech."""


def analyse_recording(audio_path: str, audio: np.ndarray, part: int, question: str) -> dict:
    """`audio` is the decoded recording (local mode); cloud mode sends the file at `audio_path`."""
    settings = get_settings()
    cloud = settings.SPEECH_MODE == "cloud"
    timings = {}

    t = time.perf_counter()
    if cloud:
        words, clean_text = stt.transcribe_groq(audio_path, settings.GROQ_API_KEY, settings.GROQ_STT_MODEL, audio)
    else:
        words, clean_text = stt.transcribe_local(audio, settings.SPEECH_STT_MODEL)
    timings["transcribe"] = round(time.perf_counter() - t, 1)
    if not any(not w.filler for w in words):
        raise NoSpeechError("We couldn't hear any speech in the recording. Check your microphone and try again.")

    fluency = analyse_fluency(words)

    # The transcript is already in hand. A pronunciation failure (Space asleep, not deployed,
    # daily GPU quota used up) must not throw it away: score everything else and say so.
    t = time.perf_counter()
    pron_error = None
    try:
        if cloud:
            pron = pronunciation_remote.assess(audio_path, words, settings.HF_SPEECH_SPACE, settings.HF_TOKEN)
        else:
            from app.speaking import pronunciation  # heavy (torch); local mode only

            pron = pronunciation.assess(audio, words, settings.SPEECH_PHONEME_MODEL)
    except SpeechServiceError as exc:
        log.warning("Pronunciation unavailable, scoring without it: %s", exc)
        pron, pron_error = PronunciationResult(accuracy=0.0, words=[]), str(exc)
    timings["pronunciation"] = round(time.perf_counter() - t, 1)

    text = scorer.text_metrics(clean_text)
    result = scorer.assess(fluency, text, pron, part, pronunciation_available=pron_error is None)
    bands = result.bands
    transcript = stt.transcript_text(words)

    measured = {"fluency": asdict(fluency), "text": asdict(text), "pronunciation_accuracy": pron.accuracy}
    t = time.perf_counter()
    review = examiner.review(question, part, transcript, measured)
    timings["examiner"] = round(time.perf_counter() - t, 1)

    feedback, corrections, upgrades = result.feedback, [], []
    if review is not None:
        bands.lexical, bands.grammar = review.lexical_band, review.grammar_band
        bands.overall = scorer.overall_band(bands)
        # Examiner tips on language first, then the audio-based tips the examiner can't give.
        audio_tips = [tip for tip in result.feedback if any(k in tip for k in ("words per minute", "paused", "filler", "Practise these words", "short ("))]
        feedback = review.feedback + audio_tips
        corrections = [c.model_dump() for c in review.corrections]
        upgrades = review.better_vocabulary
        for c in corrections:
            result.mistake_patterns.append({"type": "grammar", "label": c["explanation"], "count": 1, "examples": [c["original"]]})

    word_scores = {w.index: w for w in pron.words}
    return {
        "transcript": transcript,
        "bands": asdict(bands),
        "fluency": asdict(fluency),
        "text": asdict(text),
        "pronunciation": {
            "accuracy": pron.accuracy,
            "substitutions": pron.substitutions,
            "available": pron_error is None,
            "error": pron_error,
        },
        "words": [
            {
                "text": w.text,
                "start": round(w.start, 2),
                "end": round(w.end, 2),
                "filler": w.filler,
                "accuracy": word_scores[i].accuracy if i in word_scores else None,
                "phones": [
                    {"expected": p.expected, "heard": p.heard, "ok": p.ok} for p in word_scores[i].phones
                ] if i in word_scores and word_scores[i].accuracy < 1 else [],
            }
            for i, w in enumerate(words)
        ],
        "feedback": feedback,
        "corrections": corrections,
        "vocabulary_suggestions": upgrades,
        "mistake_patterns": result.mistake_patterns,
        "examiner": review is not None,
        "timings": timings,
    }
