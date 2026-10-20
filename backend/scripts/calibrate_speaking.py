"""Validate and calibrate speaking scores against speechocean762 (expert-rated learner English).

Runs the models locally, so first install the local-mode packages listed in requirements.txt.
1. Download https://www.openslr.org/resources/101/speechocean762.tar.gz (520 MB) and extract it.
2. Score a sample (about 4 s per recording on a laptop CPU; re-running resumes where it stopped):
       python -m scripts.calibrate_speaking run <path>/speechocean762 calib.csv 400
3. Compare with the experts:
       python -m scripts.calibrate_speaking analyse calib.csv
Then update the breakpoints in app/speaking/scorer.py (score_pronunciation).
"""
import csv
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

FIELDS = ["utt", "age", "h_accuracy", "h_fluency", "h_total", "our_accuracy", "wpm", "mlr", "pauses_pm", "asr_text", "ref_text"]


def run(root: Path, out: Path, n: int) -> None:
    from app.core.config import get_settings
    from app.speaking import pronunciation, stt
    from app.speaking.audio import load_audio
    from app.speaking.fluency import analyse

    read = lambda name: dict(l.split(maxsplit=1) for l in (root / "test" / name).read_text().splitlines() if l.strip())
    scores = json.loads((root / "resource" / "scores.json").read_text(encoding="utf-8"))
    wavs, utt2spk, ages = read("wav.scp"), read("utt2spk"), read("spk2age")
    utts = sorted(wavs)
    random.Random(762).shuffle(utts)
    done = {r["utt"] for r in csv.DictReader(out.open(encoding="utf-8"))} if out.exists() else set()
    settings = get_settings()

    with out.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not done:
            writer.writeheader()
        start = time.time()
        for i, utt in enumerate(utts[:n]):
            if utt in done:
                continue
            audio = load_audio(str(root / wavs[utt].strip()))
            words, _ = stt.transcribe_local(audio, settings.SPEECH_STT_MODEL)
            if not any(not w.filler for w in words):
                continue
            pron = pronunciation.assess(audio, words, settings.SPEECH_PHONEME_MODEL)
            flu = analyse(words)
            sc = scores[utt]
            writer.writerow({
                "utt": utt, "age": ages.get(utt2spk.get(utt, "").strip(), "").strip(),
                "h_accuracy": sc["accuracy"], "h_fluency": sc["fluency"], "h_total": sc["total"],
                "our_accuracy": pron.accuracy, "wpm": flu.words_per_minute, "mlr": flu.mean_length_of_run,
                "pauses_pm": flu.pauses_per_minute, "asr_text": " ".join(w.text for w in words), "ref_text": sc.get("text", ""),
            })
            f.flush()
            if i % 25 == 0:
                print(f"{i}/{n}  {time.time() - start:.0f}s", flush=True)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    rank = lambda x: np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    return float(np.corrcoef(rank(a), rank(b))[0, 1])


def analyse_csv(path: Path) -> None:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    col = lambda k: np.array([float(r[k]) for r in rows])
    ours, expert = col("our_accuracy"), col("h_accuracy")
    print(f"n={len(rows)}  Spearman(our accuracy, expert accuracy) = {_spearman(ours, expert):.3f}")
    print("expert accuracy -> our accuracy (median, n)")
    for lo, hi in [(0, 4), (4, 6), (6, 8), (8, 9), (9, 11)]:
        m = (expert >= lo) & (expert < hi)
        if m.any():
            print(f"  {lo}-{min(hi - 1, 10)}: {np.median(ours[m]):.3f}  (n={int(m.sum())})")


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 400)
    elif sys.argv[1:2] == ["analyse"]:
        analyse_csv(Path(sys.argv[2]))
    else:
        print(__doc__)
