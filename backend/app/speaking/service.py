"""Background processing of a speaking submission (SRS 5.2.4: STT and NLP run as background tasks).

The recording and its row are saved before analysis starts, so nothing is lost if a model
fails (NFR-3.2): the row is marked "failed" with a message the learner can read, and the
analysis can be retried.
"""
import logging
import threading
from pathlib import Path

from app.db.session import SessionLocal
from app.models import SpeakingSubmission
from app.speaking.audio import AudioError, load_audio

log = logging.getLogger(__name__)
BACKEND_DIR = Path(__file__).resolve().parents[2]

# One analysis at a time: the models are CPU-bound and share threads.
_run_lock = threading.Lock()
session_factory = SessionLocal  # tests swap this for their own session


def upload_root(upload_dir: str) -> Path:
    root = Path(upload_dir)
    return root if root.is_absolute() else BACKEND_DIR / root


def process_submission(submission_id: int, upload_dir: str) -> None:
    from app.speaking.pipeline import NoSpeechError, analyse_recording  # heavy imports, load lazily
    from app.speaking.stt import SpeechServiceError

    with _run_lock:
        db = session_factory()
        try:
            sub = db.get(SpeakingSubmission, submission_id)
            if sub is None:
                return
            sub.status, sub.error_message = "processing", None
            db.commit()
            try:
                path = str(upload_root(upload_dir) / sub.audio_file_path)
                audio = load_audio(path)  # also rejects unreadable uploads before any API call
                sub.duration_seconds = round(len(audio) / 16000, 1)
                result = analyse_recording(path, audio, sub.part_number, sub.prompt_text or "")
            except (AudioError, NoSpeechError, SpeechServiceError) as exc:
                sub.status, sub.error_message = "failed", str(exc)
                db.commit()
                return
            except Exception:
                log.exception("Speaking analysis failed for submission %s", submission_id)
                sub.status = "failed"
                sub.error_message = "Scoring failed on our side. Your recording is saved; try scoring it again."
                db.commit()
                return

            bands, fluency = result["bands"], result["fluency"]
            sub.transcribed_text = result["transcript"]
            sub.fluency_score = bands["fluency"]
            sub.lexical_score = bands["lexical"]
            sub.grammar_score = bands["grammar"]
            sub.pronunciation_score = bands["pronunciation"]
            sub.overall_band = bands["overall"]
            sub.pace_score = fluency["words_per_minute"]
            sub.filler_word_count = fluency["filler_count"]
            sub.mistake_patterns_json = result["mistake_patterns"]
            sub.analysis_json = result
            sub.status = "completed"
            db.commit()
        finally:
            db.close()


def warm_up(stt_model: str, phoneme_model: str) -> None:
    """Load the models in the background at startup, so the first learner doesn't wait for it."""
    try:
        from app.speaking import pronunciation, stt

        stt._model(stt_model)
        pronunciation._load(phoneme_model)
        pronunciation.expected_phones(["hello"])
        log.info("Speaking models ready")
    except Exception:
        log.exception("Speaking model warm-up failed; models will load on first use")
