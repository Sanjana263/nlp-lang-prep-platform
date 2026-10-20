"""Decode any browser recording (webm/opus, ogg, mp4/aac, wav) to 16 kHz mono float32.

PyAV ships its own FFmpeg, so no system install is needed.
"""
import av
import numpy as np

SAMPLE_RATE = 16000


class AudioError(ValueError):
    """The upload is not audio we can read."""


def load_audio(path: str) -> np.ndarray:
    try:
        container = av.open(path)
    except Exception as exc:  # av raises many specific errors; all mean "unreadable"
        raise AudioError("The recording could not be read. Try recording again.") from exc
    with container:
        if not container.streams.audio:
            raise AudioError("The upload has no audio track.")
        resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
        chunks = [f.to_ndarray().reshape(-1) for frame in container.decode(audio=0) for f in resampler.resample(frame)]
        chunks += [f.to_ndarray().reshape(-1) for f in resampler.resample(None)]
    if not chunks:
        raise AudioError("The recording is empty.")
    return np.concatenate(chunks).astype(np.float32)


def duration_seconds(audio: np.ndarray) -> float:
    return len(audio) / SAMPLE_RATE
