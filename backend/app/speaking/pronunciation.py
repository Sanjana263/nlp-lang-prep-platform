"""Phoneme-level pronunciation scoring.

Method (CTC "goodness of pronunciation", as in the 2025 GOP-CTC literature):
  1. A wav2vec2 phoneme recogniser (fine-tuned on espeak phone labels) gives per-frame
     phone log-probabilities for the whole answer.
  2. For each spoken word, espeak-ng gives the expected phones, in both US and UK English.
  3. The expected phones are force-aligned (CTC Viterbi) to that word's frames. A phone's
     GOP is how far its log-probability sits below the best competing phone on its frames;
     the competing phone is what the learner most likely said instead.
  4. Phones whose substitute is an accent variant (e.g. Indian-English retroflex t, US
     flap t) count as correct: IELTS rewards intelligibility, not a particular accent.
"""
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, field

import numpy as np

from .audio import SAMPLE_RATE
from .fluency import Word

FRAME_SECONDS = 0.02         # wav2vec2 emits one frame per 20 ms
GOP_OK = -1.5                # log-prob gap above which a phone counts as said correctly
GOP_OK_L2 = -0.5             # stricter for well-known learner confusions (close phones score close)
CHUNK_SECONDS = 20.0         # recogniser runs on <=20 s pieces to keep memory flat
WINDOW_BEFORE = 0.06         # seconds of context around each word: word-final phones often
WINDOW_AFTER = 0.14          # run past the timestamp Whisper gives

# Pairs that differ by accent rather than error (checked both ways).
_ACCENT_PAIRS = [
    ("ɹ", "r"), ("ɹ", "ɻ"), ("ɹ", "ɾ"),
    ("t", "ʈ"), ("t", "ɾ"), ("t", "ʔ"), ("d", "ɖ"), ("d", "ɾ"), ("n", "ɳ"), ("l", "ɫ"),
    ("v", "ʋ"), ("w", "ʋ"),
    ("ə", "ɐ"), ("ə", "ɚ"), ("ə", "ʌ"), ("ə", "ɪ"), ("ə", "ʊ"), ("ɚ", "ɜː"), ("ʌ", "ɐ"), ("ʌ", "ɑ"),
    ("ɜː", "ɜ"), ("ɑː", "ɑ"), ("ɑː", "a"), ("ɑː", "ɒ"), ("ɒ", "ɔ"), ("ɒ", "ɑ"), ("ɔː", "ɔ"), ("ɔː", "oː"),
    ("oʊ", "əʊ"), ("oʊ", "oː"), ("oʊ", "o"), ("əʊ", "oː"), ("əʊ", "o"),
    ("eɪ", "e"), ("eɪ", "eː"), ("ɛ", "e"), ("æ", "a"), ("æ", "ɛ"),
    ("i", "iː"), ("i", "ɪ"), ("uː", "u"), ("ʊ", "u"), ("aɪ", "a"), ("ɛɹ", "ɛː"), ("ɪɹ", "ɪə"), ("ʊɹ", "ʊə"),
    ("ɔː", "ɑː"), ("ɔ", "ɑ"), ("iə", "iː"), ("ɪə", "iː"), ("ɪə", "iə"),  # cot-caught merger, NEAR vowel
]

# Function words are usually said in their weak form in connected speech ("a" /ə/, "to" /tə/);
# espeak gives the dictionary form for a word on its own, so add the weak forms as variants.
WEAK_FORMS = {
    "a": ["ə"], "an": ["ə n"], "the": ["ð ə", "ð i"], "and": ["ə n d", "ə n", "n"], "to": ["t ə", "t ʊ"],
    "of": ["ə v", "ə"], "for": ["f ɚ", "f ə"], "from": ["f ɹ ə m"], "at": ["ə t"], "as": ["ə z"],
    "can": ["k ə n"], "but": ["b ə t"], "that": ["ð ə t"], "was": ["w ə z"], "were": ["w ɚ", "w ə"],
    "have": ["h ə v", "ə v"], "has": ["h ə z"], "had": ["h ə d"], "do": ["d ə"], "does": ["d ə z"],
    "are": ["ɚ", "ə"], "you": ["j ə"], "your": ["j ɚ", "j ə"], "some": ["s ə m"], "them": ["ð ə m"],
    "or": ["ɚ"], "would": ["w ə d"], "could": ["k ə d"], "should": ["ʃ ə d"], "must": ["m ə s t"],
}
ACCENT_OK = {pair for a, b in _ACCENT_PAIRS for pair in ((a, b), (b, a))}

# Substitutions that are common for learners of English and change meaning ("tree" for "three").
_L2_CONFUSIONS = [
    ("θ", "t"), ("θ", "s"), ("θ", "f"), ("ð", "d"), ("ð", "z"), ("v", "w"), ("v", "b"), ("v", "f"),
    ("ʃ", "s"), ("z", "s"), ("ʒ", "z"), ("dʒ", "z"), ("p", "f"), ("ŋ", "n"), ("l", "ɹ"),
    ("iː", "ɪ"), ("æ", "ɛ"), ("ʌ", "ɑː"),
]
L2_CONFUSION = {pair for a, b in _L2_CONFUSIONS for pair in ((a, b), (b, a))}


@dataclass
class PhoneResult:
    expected: str
    heard: str
    ok: bool


@dataclass
class WordPronunciation:
    index: int                     # position in the transcript word list
    word: str
    accuracy: float                # share of phones said correctly
    phones: list[PhoneResult]


@dataclass
class PronunciationResult:
    accuracy: float                # over all scored phones
    words: list[WordPronunciation]
    substitutions: dict[str, list[str]] = field(default_factory=dict)  # "θ→t" -> example words

    @property
    def scored(self) -> bool:
        return bool(self.words)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PronunciationResult":
        words = [
            WordPronunciation(index=w["index"], word=w["word"], accuracy=w["accuracy"],
                              phones=[PhoneResult(**p) for p in w["phones"]])
            for w in d.get("words", [])
        ]
        return cls(accuracy=d.get("accuracy", 0.0), words=words, substitutions=d.get("substitutions", {}))


# ------------------------------------------------------------------ model loading
_lock = threading.Lock()
_model = None
_processor = None
_phonemizers: dict = {}


def _ensure_espeak():
    """Point phonemizer at the espeak-ng library bundled by espeakng-loader (no system install)."""
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())


def _load(model_name: str):
    global _model, _processor
    with _lock:
        if _model is None:
            _ensure_espeak()  # the model's tokenizer starts espeak on load
            from transformers import AutoModelForCTC, AutoProcessor
            _processor = AutoProcessor.from_pretrained(model_name)
            _model = AutoModelForCTC.from_pretrained(model_name).eval()
    return _model, _processor


def _phonemizer(lang: str):
    if lang not in _phonemizers:
        from phonemizer.backend import EspeakBackend

        _ensure_espeak()
        _phonemizers[lang] = EspeakBackend(lang, with_stress=False)
    return _phonemizers[lang]


def expected_phones(words: list[str]) -> dict[str, list[list[str]]]:
    """word -> list of phone sequences (one per accent variant)."""
    from phonemizer.separator import Separator

    sep = Separator(phone=" ", word="|")
    unique = sorted(set(words))
    variants: dict[str, list[list[str]]] = defaultdict(list)
    for lang in ("en-us", "en-gb"):
        out = _phonemizer(lang).phonemize(unique, separator=sep, strip=True)
        for word, phones in zip(unique, out):
            seq = phones.replace("|", " ").split()
            if seq and seq not in variants[word]:
                variants[word].append(seq)
    for word in unique:
        for weak in WEAK_FORMS.get(word, []):
            variants[word].append(weak.split())
    return variants


# ------------------------------------------------------------------ recogniser
def phone_log_probs(audio: np.ndarray, words: list[Word], model_name: str) -> np.ndarray:
    """(frames, vocab) log-probabilities for the whole recording, computed in chunks cut at pauses."""
    import torch

    model, processor = _load(model_name)
    cuts = [0]
    for prev, cur in zip(words, words[1:]):
        if (cur.start - cuts[-1] / SAMPLE_RATE) > CHUNK_SECONDS:
            cuts.append(int(((prev.end + cur.start) / 2) * SAMPLE_RATE))
    cuts.append(len(audio))

    parts = []
    with torch.inference_mode():
        for a, b in zip(cuts, cuts[1:]):
            piece = audio[a:b]
            if len(piece) < SAMPLE_RATE // 10:
                continue
            inputs = processor(piece, sampling_rate=SAMPLE_RATE, return_tensors="pt").input_values
            logits = model(inputs.to(model.device)).logits[0]  # model may sit on a GPU (the Space)
            lp = torch.log_softmax(logits.float(), dim=-1).cpu().numpy()
            # pad/trim so frame indices stay aligned with absolute time
            start_frame = int(round(a / SAMPLE_RATE / FRAME_SECONDS))
            if parts:
                have = sum(len(p) for p in parts)
                if have < start_frame:
                    parts.append(np.tile(lp[:1], (start_frame - have, 1)))
                elif have > start_frame:
                    lp = lp[have - start_frame:]
            parts.append(lp)
    return np.concatenate(parts) if parts else np.zeros((0, 1), dtype=np.float32)


def ctc_align(lp: np.ndarray, labels: list[int], blank: int = 0) -> list[list[int]] | None:
    """Viterbi CTC forced alignment. Returns, per label, the frames assigned to it."""
    T, n = len(lp), len(labels)
    if n == 0 or T < n:
        return None
    states = [blank]
    for lab in labels:
        states += [lab, blank]
    S = len(states)
    neg = -1e9
    dp = np.full((T, S), neg)
    back = np.zeros((T, S), dtype=np.int8)  # 0 stay, 1 from s-1, 2 from s-2
    dp[0, 0] = lp[0, states[0]]
    dp[0, 1] = lp[0, states[1]]
    for t in range(1, T):
        prev = dp[t - 1]
        for s in range(S):
            best, move = prev[s], 0
            if s >= 1 and prev[s - 1] > best:
                best, move = prev[s - 1], 1
            if s >= 2 and states[s] != blank and states[s] != states[s - 2] and prev[s - 2] > best:
                best, move = prev[s - 2], 2
            dp[t, s] = best + lp[t, states[s]]
            back[t, s] = move
    s = S - 1 if dp[T - 1, S - 1] >= dp[T - 1, S - 2] else S - 2
    if dp[T - 1, s] <= neg / 2:
        return None
    frames: list[list[int]] = [[] for _ in labels]
    for t in range(T - 1, -1, -1):
        if s % 2 == 1:
            frames[s // 2].append(t)
        s -= int(back[t, s])
    return frames


def _score_word(lp: np.ndarray, seq: list[str], vocab: dict[str, int], id_to_phone: dict[int, str], blank: int):
    ids = [vocab[p] for p in seq if p in vocab]
    if len(ids) != len(seq):
        return None
    frames = ctc_align(lp, ids, blank)
    if frames is None:
        return None
    competitors = lp.copy()
    competitors[:, blank] = -np.inf
    phones, gops = [], []
    for phone, pid, fr in zip(seq, ids, frames):
        # Score each phone on its best frame: CTC output is "peaky", so a phone that was said
        # is the top choice on at least one frame, and extra frames at the edges don't hurt.
        margins = lp[fr, pid] - competitors[fr].max(axis=1)
        k = int(np.argmax(margins))
        gop = float(margins[k])
        heard = id_to_phone.get(int(competitors[fr[k]].argmax()), phone)
        threshold = GOP_OK_L2 if (phone, heard) in L2_CONFUSION else GOP_OK
        ok = gop > threshold or heard == phone or (phone, heard) in ACCENT_OK
        phones.append(PhoneResult(expected=phone, heard=phone if ok else heard, ok=ok))
        gops.append(gop)
    return phones, float(np.mean(gops))


def assess(audio: np.ndarray, words: list[Word], model_name: str, lp: np.ndarray | None = None) -> PronunciationResult:
    """`lp` can be passed in when the recogniser ran elsewhere (the Space runs it on a GPU)."""
    content = [(i, w) for i, w in enumerate(words) if not w.filler and w.clean.strip("'-")]
    if not content:
        return PronunciationResult(accuracy=0.0, words=[])

    if lp is None:
        lp = phone_log_probs(audio, words, model_name)
    _, processor = _load(model_name)
    vocab = processor.tokenizer.get_vocab()
    id_to_phone = {i: p for p, i in vocab.items()}
    blank = vocab.get(processor.tokenizer.pad_token, 0)
    variants = expected_phones([w.clean for _, w in content])

    results: list[WordPronunciation] = []
    subs: dict[str, list[str]] = defaultdict(list)
    for index, w in content:
        a = max(0, int((w.start - WINDOW_BEFORE) / FRAME_SECONDS))
        b = min(len(lp), int((w.end + WINDOW_AFTER) / FRAME_SECONDS) + 1)
        window = lp[a:b]
        best = None
        for seq in variants.get(w.clean, []):
            scored = _score_word(window, seq, vocab, id_to_phone, blank)
            if scored and (best is None or scored[1] > best[1]):
                best = scored
        if best is None:
            continue
        phones = best[0]
        acc = sum(p.ok for p in phones) / len(phones)
        results.append(WordPronunciation(index=index, word=w.text.strip(), accuracy=round(acc, 2), phones=phones))
        for p in phones:
            if not p.ok:
                key = f"{p.expected}→{p.heard}"
                if w.clean not in subs[key]:
                    subs[key].append(w.clean)

    total = sum(len(r.phones) for r in results)
    correct = sum(p.ok for r in results for p in r.phones)
    ranked = dict(sorted(subs.items(), key=lambda kv: -len(kv[1])))
    return PronunciationResult(accuracy=round(correct / total, 3) if total else 0.0, words=results, substitutions=ranked)
