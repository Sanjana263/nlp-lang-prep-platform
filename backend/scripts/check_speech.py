"""Find out why speech-to-text or pronunciation isn't working, one stage at a time.

Run from the repo root:   npm run check-speech -- path/to/recording.webm
(or from backend/:        python -m scripts.check_speech path/to/recording.webm)

With no file it only checks your keys and that Groq accepts them. With a recording (any
format the browser produces, or a .wav/.mp3) it also decodes it, transcribes it and checks
pronunciation, and tells you which stage failed and why.
Recordings the app saved are in backend/uploads/speaking/<user id>/.
"""
import sys
import time

from app.core.config import get_settings


def step(name: str) -> None:
    print(f"\n== {name}")


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else None
    s = get_settings()

    step("1. Settings (backend/.env)")
    print(f"SPEECH_MODE     = {s.SPEECH_MODE}")
    print(f"GROQ_API_KEY    = {'set (' + str(len(s.GROQ_API_KEY.strip())) + ' chars)' if s.GROQ_API_KEY.strip() else 'MISSING'}")
    print(f"HF_TOKEN        = {'set' if s.HF_TOKEN.strip() else 'missing'}")
    print(f"HF_SPEECH_SPACE = {s.HF_SPEECH_SPACE or 'missing'}")
    if s.SPEECH_MODE != "cloud":
        print("SPEECH_MODE is not 'cloud'; this script only checks the cloud setup.")
        return

    import numpy as np

    from app.speaking import stt
    from app.speaking.audio import AudioError, load_audio
    from app.speaking.fluency import analyse
    from app.speaking.stt import SpeechServiceError

    step("2. Recording")
    if path:
        try:
            audio = load_audio(path)
        except AudioError as exc:
            sys.exit(f"FAILED to decode the file: {exc}")
        print(f"decoded OK: {len(audio) / 16000:.1f} s, loudest sample {float(np.abs(audio).max()):.2f}")
        if float(np.abs(audio).max()) < 0.01:
            print("WARNING: the recording is almost silent. Check the microphone / input device.")
    else:
        print("no file given; sending 1 s of silence just to test the key")
        audio = np.zeros(16000, dtype=np.float32)

    step("3. Speech-to-text (Groq)")
    t = time.perf_counter()
    try:
        words, text = stt.transcribe_groq(path or "", s.GROQ_API_KEY, s.GROQ_STT_MODEL, audio)
    except SpeechServiceError as exc:
        sys.exit(f"FAILED: {exc}")
    print(f"answered in {time.perf_counter() - t:.1f} s; {len(words)} words")
    print(f"text: {text[:300] or '(nothing recognised)'}")
    if path and not words:
        sys.exit("Groq accepted the file but heard no speech. Record again, closer to the microphone.")
    if words:
        print("fluency:", analyse(words))

    step("4. Pronunciation (Hugging Face Space)")
    if not path or not words:
        print("skipped (needs a recording with speech)")
        return
    from app.speaking import pronunciation_remote

    t = time.perf_counter()
    try:
        res = pronunciation_remote.assess(path, words, s.HF_SPEECH_SPACE, s.HF_TOKEN)
    except SpeechServiceError as exc:
        print(f"FAILED: {exc}\n(Transcription still works; the app now scores the answer without pronunciation.)")
        return
    print(f"answered in {time.perf_counter() - t:.1f} s; sounds said clearly: {res.accuracy:.0%}")


if __name__ == "__main__":
    main()
