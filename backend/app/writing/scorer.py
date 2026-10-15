import math
from typing import List, Tuple
from app.writing.schemas import EssayMetrics, BandScores


def round_band(score: float) -> float:
    """IELTS-style rounding: nearest 0.5, kept between 4.0 and 9.0."""
    rounded = math.floor(score * 2 + 0.5) / 2
    return max(4.0, min(9.0, rounded))


def score_task_response(m: EssayMetrics) -> float:
    # Proxy: essay length. IELTS Task 2 needs 250+ words.
    wc = m.word_count
    if wc < 150:
        return 4.0
    if wc < 200:
        return 5.0
    if wc < 250:
        return 5.5
    if wc < 300:
        return 6.5
    return 7.0


def score_coherence(m: EssayMetrics) -> float:
    # Proxy: sentence length. Very short or very long sentences read badly.
    length = m.avg_sentence_length
    if 15 <= length <= 25:
        return 7.0
    if 12 <= length < 15 or 25 < length <= 30:
        return 6.0
    return 5.0


def score_vocabulary(m: EssayMetrics) -> float:
    # Short essays always look "diverse", so we cap them.
    if m.word_count < 150:
        return 5.0
    d = m.lexical_diversity
    if d >= 0.60:
        return 7.5
    if d >= 0.50:
        return 7.0
    if d >= 0.42:
        return 6.0
    if d >= 0.35:
        return 5.5
    return 5.0


def score_grammar(m: EssayMetrics) -> float:
    # Uses the dependency parsing results.
    r = m.complex_sentence_ratio
    if r >= 0.60:
        score = 7.0
    elif r >= 0.40:
        score = 6.5
    elif r >= 0.25:
        score = 6.0
    else:
        score = 5.0
    if m.avg_parse_depth >= 3:
        score += 0.5
    return score


def build_feedback(m: EssayMetrics) -> List[str]:
    tips = []
    if m.word_count < 250:
        tips.append(
            f"Your essay has {m.word_count} words. IELTS Task 2 needs at least 250."
        )
    if m.avg_sentence_length < 12:
        tips.append("Your sentences are short. Join ideas using linking words.")
    elif m.avg_sentence_length > 30:
        tips.append("Your sentences are very long. Split some for clarity.")
    if m.complex_sentence_ratio < 0.25:
        tips.append(
            "Use more complex sentences with 'although', 'because', 'which', 'who'."
        )
    if m.word_count >= 150 and m.lexical_diversity < 0.40:
        tips.append("You repeat many words. Try synonyms and varied vocabulary.")
    if not tips:
        tips.append("Good structure. Keep practising with different topics.")
    return tips


def score_essay(m: EssayMetrics) -> Tuple[BandScores, List[str]]:
    tr = score_task_response(m)
    cc = score_coherence(m)
    lr = score_vocabulary(m)
    gra = score_grammar(m)
    overall = round_band((tr + cc + lr + gra) / 4)

    bands = BandScores(
        task_response=tr,
        coherence=cc,
        vocabulary=lr,
        grammar=gra,
        overall=overall,
    )
    return bands, build_feedback(m)