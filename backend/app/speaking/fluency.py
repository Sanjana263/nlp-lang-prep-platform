"""Fluency measures from word timings.

The measures are the ones research ties most closely to human fluency ratings
(Suzuki et al. 2021 meta-analysis: speech rate r≈.76, mean length of run r≈.72,
pause frequency r≈-.59), plus filler words and repetitions, which IELTS
descriptors name directly ("hesitation", "repetition", "self-correction").
"""
import re
from dataclasses import dataclass

FILLERS = {"um", "umm", "uh", "uhm", "uhh", "er", "erm", "ah", "eh", "hmm", "mm", "mhm"}
SILENT_PAUSE = 0.25   # seconds; the conventional threshold for a silent pause (ends a run)
NOTICEABLE_PAUSE = 0.5  # seconds; counted for pause frequency
LONG_PAUSE = 1.0      # seconds; a clear break in speech


@dataclass
class Word:
    text: str
    start: float
    end: float
    filler: bool = False

    @property
    def clean(self) -> str:
        return re.sub(r"[^\w'-]", "", self.text).lower()


def mark_fillers(words: list[Word]) -> list[Word]:
    for w in words:
        w.filler = w.clean in FILLERS
    return words


@dataclass
class FluencyMetrics:
    speaking_seconds: float      # first word start to last word end
    word_count: int              # excluding fillers
    words_per_minute: float
    articulation_rate: float     # words per minute of actual speaking (pauses removed)
    mean_length_of_run: float    # words between silent pauses
    pauses_per_minute: float     # pauses of 0.5 s or more, per minute
    long_pauses: int             # pauses of 1 s or more
    filler_count: int
    fillers_per_100_words: float
    repetitions: int             # immediate word repetitions ("the the")


def analyse(words: list[Word]) -> FluencyMetrics:
    spoken = [w for w in words if w.end > w.start or w.clean]
    content = [w for w in spoken if not w.filler and w.clean]
    if not content:
        return FluencyMetrics(0.0, 0, 0.0, 0.0, 0.0, 0.0, 0, len(spoken), 0.0, 0)

    total = max(spoken[-1].end - spoken[0].start, 0.1)
    minutes = total / 60

    # Gaps between consecutive words (fillers count as hesitation, so they break runs too).
    # Pauses are counted wherever they fall: Whisper adds a full stop at most pauses,
    # so punctuation cannot tell a planned pause from a mid-sentence one.
    runs, run, noticeable, long_pauses, pause_time = [], 0, 0, 0, 0.0
    for prev, cur in zip(spoken, spoken[1:]):
        if not prev.filler:
            run += 1
        gap = cur.start - prev.end
        if gap >= SILENT_PAUSE or cur.filler:
            if run:
                runs.append(run)
            run = 0
        if gap >= SILENT_PAUSE:
            pause_time += gap
            if gap >= NOTICEABLE_PAUSE:
                noticeable += 1
            if gap >= LONG_PAUSE:
                long_pauses += 1
    if not spoken[-1].filler:
        run += 1
    if run:
        runs.append(run)

    repetitions = sum(1 for a, b in zip(content, content[1:]) if a.clean == b.clean and len(a.clean) > 1)
    fillers = sum(1 for w in spoken if w.filler)
    phonation = max(total - pause_time, 0.1)

    return FluencyMetrics(
        speaking_seconds=round(total, 1),
        word_count=len(content),
        words_per_minute=round(len(content) / minutes, 1),
        articulation_rate=round(len(content) / (phonation / 60), 1),
        mean_length_of_run=round(sum(runs) / len(runs), 1) if runs else float(len(content)),
        pauses_per_minute=round(noticeable / minutes, 1),
        long_pauses=long_pauses,
        filler_count=fillers,
        fillers_per_100_words=round(100 * fillers / len(content), 1),
        repetitions=repetitions,
    )
