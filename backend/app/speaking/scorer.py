"""Map measured features to the four IELTS Speaking criteria.

Fluency & coherence and Pronunciation come from the audio (timings, phonemes).
Lexical resource and Grammatical range come from the transcript. When the optional
LLM examiner is configured it refines the two text-based criteria (it can spot actual
errors); it never scores fluency or pronunciation, because it only sees text.

The breakpoints below are heuristic, informed by L2 fluency research and IELTS band
descriptors. They are kept in one place so they can be recalibrated against rated data.
"""
from dataclasses import dataclass, field

from wordfreq import zipf_frequency

from app.speaking.fluency import FluencyMetrics
from app.speaking.pronunciation import PronunciationResult
from app.writing.analyzer import has_subordinate_clause, nlp, sentence_depth

MIN_WORDS = {1: 25, 2: 100, 3: 50}         # below this, the answer was too short to show range
DISCOURSE_MARKERS = {
    "because", "however", "although", "though", "so", "therefore", "moreover", "also", "actually",
    "for example", "for instance", "on the other hand", "in my opinion", "i think", "firstly", "first of all",
    "secondly", "finally", "whereas", "while", "as a result", "in addition", "basically", "especially",
}
RARE_ZIPF = 4.5                             # rarer than roughly 30 per million words
CONTENT_POS = {"NOUN", "VERB", "ADJ", "ADV"}


def band(x: float, points: list[tuple[float, float]]) -> float:
    """Piecewise-linear map from a measure to a band; points are (measure, band), any order."""
    pts = sorted(points)
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def round_band(score: float) -> float:
    return max(1.0, min(9.0, int(score * 2 + 0.5) / 2))


@dataclass
class TextMetrics:
    word_count: int
    mattr: float                  # moving-average type-token ratio (length-independent diversity)
    rare_word_ratio: float        # share of content words rarer than everyday vocabulary
    rare_words: list[str]
    complex_sentence_ratio: float
    avg_parse_depth: float
    discourse_markers: list[str]


@dataclass
class SpeakingBands:
    fluency: float
    lexical: float
    grammar: float
    pronunciation: float
    overall: float


@dataclass
class Assessment:
    bands: SpeakingBands
    feedback: list[str]
    mistake_patterns: list[dict] = field(default_factory=list)


def text_metrics(transcript: str) -> TextMetrics:
    doc = nlp(transcript)
    tokens = [t for t in doc if t.is_alpha]
    lemmas = [t.lemma_.lower() for t in tokens]
    window = 40
    if len(lemmas) <= window:
        mattr = len(set(lemmas)) / len(lemmas) if lemmas else 0.0
    else:
        ratios = [len(set(lemmas[i:i + window])) / window for i in range(len(lemmas) - window + 1)]
        mattr = sum(ratios) / len(ratios)

    content = [t for t in tokens if t.pos_ in CONTENT_POS and not t.is_stop]
    rare = sorted({t.lemma_.lower() for t in content if zipf_frequency(t.lemma_.lower(), "en") < RARE_ZIPF})
    rare_count = sum(1 for t in content if t.lemma_.lower() in rare)

    sents = [s for s in doc.sents if any(t.is_alpha for t in s)]
    lowered = " " + " ".join(lemmas) + " "
    markers = sorted(m for m in DISCOURSE_MARKERS if f" {m} " in lowered)
    return TextMetrics(
        word_count=len(tokens),
        mattr=round(mattr, 3),
        rare_word_ratio=round(rare_count / len(content), 3) if content else 0.0,
        rare_words=rare[:12],
        complex_sentence_ratio=round(sum(has_subordinate_clause(s) for s in sents) / len(sents), 2) if sents else 0.0,
        avg_parse_depth=round(sum(sentence_depth(s) for s in sents) / len(sents), 2) if sents else 0.0,
        discourse_markers=markers,
    )


def score_fluency(f: FluencyMetrics, t: TextMetrics, part: int) -> float:
    rate = band(f.words_per_minute, [(60, 4), (90, 5), (110, 6), (130, 7), (150, 8), (170, 8.5)])
    # MLR here is in words (literature often uses syllables, about 1.4 per word)
    runs = band(f.mean_length_of_run, [(2, 4), (3.5, 5), (5, 6), (7, 7), (9, 8), (12, 8.5)])
    pauses = band(f.pauses_per_minute, [(20, 4), (15, 5), (10, 6), (6, 7), (3, 8), (1, 8.5)])
    fillers = band(f.fillers_per_100_words, [(10, 4), (7, 5), (4.5, 6), (2.5, 7), (1, 8), (0, 8.5)])
    linking = band(len(t.discourse_markers), [(0, 5), (2, 6), (4, 7), (6, 8)])
    score = 0.25 * rate + 0.25 * runs + 0.2 * pauses + 0.15 * fillers + 0.15 * linking
    if f.word_count and f.repetitions / f.word_count > 0.03:
        score -= 0.5
    if t.word_count < MIN_WORDS.get(part, 25):
        score = min(score, 5.0)
    return score


def score_lexical(t: TextMetrics, part: int) -> float:
    diversity = band(t.mattr, [(0.55, 4.5), (0.65, 5.5), (0.72, 6.5), (0.78, 7.5), (0.84, 8.5)])
    range_ = band(t.rare_word_ratio, [(0.03, 4.5), (0.07, 5.5), (0.12, 6.5), (0.18, 7.5), (0.25, 8.5)])
    score = 0.5 * diversity + 0.5 * range_
    return min(score, 5.0) if t.word_count < MIN_WORDS.get(part, 25) else score


def score_grammar(t: TextMetrics) -> float:
    complexity = band(t.complex_sentence_ratio, [(0.1, 4.5), (0.25, 5.5), (0.4, 6.5), (0.55, 7.5), (0.7, 8.5)])
    depth = band(t.avg_parse_depth, [(2, 4.5), (3, 5.5), (4, 6.5), (5, 7.5), (6, 8.5)])
    # Without an error check (the optional LLM examiner) we only see range, so cap it.
    return min(0.6 * complexity + 0.4 * depth, 8.0)


def score_pronunciation(p: PronunciationResult) -> float:
    if not p.scored:
        return 4.0
    # Fitted on speechocean762 (expert-rated learner speech): median share of sounds we judge
    # correct is ~0.91 for experts' 9-10/10, ~0.84 for 8, ~0.78 for 6-7, ~0.65 for 4-5.
    # Expert scale mapped to IELTS bands: 9-10 -> 8+, 8 -> 7, 6-7 -> 6, 4-5 -> 5, <=3 -> 4.
    # First pass on 55 utterances (Spearman ~0.4 with expert accuracy); rerun
    # scripts/calibrate_speaking.py on more data to refine.
    return band(p.accuracy, [(0.50, 4), (0.65, 5), (0.78, 6), (0.85, 7), (0.91, 8), (0.96, 9)])


def mistake_patterns(f: FluencyMetrics, p: PronunciationResult) -> list[dict]:
    patterns = []
    for pair, words in list(p.substitutions.items())[:6]:
        expected, heard = pair.split("→")
        patterns.append({
            "type": "pronunciation", "label": f"/{expected}/ said as /{heard}/",
            "count": len(words), "examples": words[:4],
        })
    if f.fillers_per_100_words >= 4.5:
        patterns.append({"type": "fluency", "label": "Frequent filler words", "count": f.filler_count, "examples": []})
    if f.long_pauses >= 3:
        patterns.append({"type": "fluency", "label": "Long pauses", "count": f.long_pauses, "examples": []})
    if f.repetitions >= 3:
        patterns.append({"type": "fluency", "label": "Repeated words", "count": f.repetitions, "examples": []})
    return patterns


def build_feedback(f: FluencyMetrics, t: TextMetrics, p: PronunciationResult, part: int) -> list[str]:
    tips = []
    if t.word_count < MIN_WORDS.get(part, 25):
        target = {1: "two or three sentences", 2: "the full two minutes", 3: "a developed answer with reasons and examples"}[part]
        tips.append(f"Your answer was short ({t.word_count} words). Aim for {target}, so the examiner can hear your range.")
    if f.words_per_minute and f.words_per_minute < 100:
        tips.append(f"You spoke at {f.words_per_minute:.0f} words per minute. Confident speakers are usually around 120–150; practise answering without stopping to plan each sentence.")
    if f.pauses_per_minute >= 10 or f.long_pauses >= 3:
        tips.append("You paused often while speaking. Plan the next idea while you finish the current one, and use phrases like \"let me think\" to fill thinking time naturally.")
    if f.fillers_per_100_words >= 4.5:
        tips.append(f"You used {f.filler_count} filler sounds (um, uh). Replace them with a short silent pause or a linking phrase.")
    if len(t.discourse_markers) < 2:
        tips.append("Link your ideas with words such as because, however, for example and on the other hand.")
    if t.rare_word_ratio < 0.07:
        tips.append("Your vocabulary is mostly everyday words. Try more precise words for the topic, for example \"crucial\" instead of \"very important\".")
    if t.complex_sentence_ratio < 0.25:
        tips.append("Most of your sentences are simple. Add clauses with which, who, when, although or if.")
    worst = sorted((w for w in p.words if w.accuracy < 0.7 and len(w.phones) >= 3), key=lambda w: w.accuracy)[:4]
    if worst:
        tips.append("Practise these words, which were hard to recognise: " + ", ".join(w.word.strip(".,!?") for w in worst) + ".")
    if not tips:
        tips.append("A strong answer. Keep practising with Part 3 questions to build more abstract, extended answers.")
    return tips


def assess(f: FluencyMetrics, t: TextMetrics, p: PronunciationResult, part: int) -> Assessment:
    fc, lr, gra, pr = score_fluency(f, t, part), score_lexical(t, part), score_grammar(t), score_pronunciation(p)
    bands = SpeakingBands(
        fluency=round_band(fc), lexical=round_band(lr), grammar=round_band(gra), pronunciation=round_band(pr),
        overall=round_band((fc + lr + gra + pr) / 4),
    )
    return Assessment(bands=bands, feedback=build_feedback(f, t, p, part), mistake_patterns=mistake_patterns(f, p))
