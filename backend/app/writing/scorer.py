import math
from typing import List, Tuple
from app.writing.schemas import EssayMetrics, BandScores


def round_band(score: float) -> float:
    """IELTS-style rounding: nearest 0.5, kept between 4.0 and 9.0."""
    rounded = math.floor(score * 2 + 0.5) / 2
    return max(4.0, min(9.0, rounded))


def score_task_response(m: EssayMetrics, min_words: int) -> float:
    # Proxy: length compared with the minimum for this writing type
    ratio = m.word_count / min_words
    if ratio < 0.6:
        return 4.0
    if ratio < 0.8:
        return 5.0
    if ratio < 1.0:
        return 5.5
    if ratio < 1.2:
        return 6.5
    return 7.0


def score_coherence(m: EssayMetrics) -> float:
    length = m.avg_sentence_length
    if 15 <= length <= 25:
        return 7.0
    if 12 <= length < 15 or 25 < length <= 30:
        return 6.0
    return 5.0


def score_vocabulary(m: EssayMetrics) -> float:
    if m.word_count < 100:
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


def grammar_penalty(m: EssayMetrics, issue_count: int) -> float:
    """Take marks off when the rule checks find many mistakes."""
    if m.word_count == 0:
        return 0.0
    per_100_words = issue_count / m.word_count * 100
    if per_100_words >= 6:
        return 1.0
    if per_100_words >= 3:
        return 0.5
    return 0.0


def score_grammar(m: EssayMetrics, issue_count: int) -> float:
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
    return max(4.0, score - grammar_penalty(m, issue_count))


def build_feedback(m: EssayMetrics, min_words: int) -> List[str]:
    tips = []
    if m.word_count < min_words:
        tips.append(f"Your text has {m.word_count} words. This writing type needs at least {min_words}.")
    if m.avg_sentence_length < 12:
        tips.append("Your sentences are short. Join ideas using linking words.")
    elif m.avg_sentence_length > 30:
        tips.append("Your sentences are very long. Split some for clarity.")
    if m.complex_sentence_ratio < 0.25:
        tips.append("Use more complex sentences with 'although', 'because', 'which', 'who'.")
    if m.word_count >= 100 and m.lexical_diversity < 0.40:
        tips.append("You repeat many words. Try synonyms and varied vocabulary.")
    return tips


def score_essay(m: EssayMetrics, min_words: int, issue_count: int) -> Tuple[BandScores, List[str]]:
    tr = score_task_response(m, min_words)
    cc = score_coherence(m)
    lr = score_vocabulary(m)
    gra = score_grammar(m, issue_count)
    overall = round_band((tr + cc + lr + gra) / 4)
    bands = BandScores(task_response=tr, coherence=cc, vocabulary=lr, grammar=gra, overall=overall)
    return bands, build_feedback(m, min_words)