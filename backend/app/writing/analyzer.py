import spacy
from app.writing.schemas import EssayMetrics

# Load the English model once, when the server starts
nlp = spacy.load("en_core_web_sm")

# Dependency labels that mark a subordinate or complex clause
SUBORDINATE_DEPS = {"advcl", "ccomp", "xcomp", "relcl", "acl", "csubj"}


def token_depth(token) -> int:
    """How many steps from this word up to the root of the sentence."""
    depth = 0
    while token.head != token:
        token = token.head
        depth += 1
    return depth


def sentence_depth(sent) -> int:
    """Depth of the dependency tree = deepest word in the sentence."""
    return max(token_depth(t) for t in sent)


def has_subordinate_clause(sent) -> bool:
    return any(t.dep_ in SUBORDINATE_DEPS for t in sent)


def analyze_essay(text: str) -> EssayMetrics:
    doc = nlp(text)
    sentences = list(doc.sents)
    words = [t for t in doc if t.is_alpha]

    word_count = len(words)
    sentence_count = len(sentences)

    if word_count == 0 or sentence_count == 0:
        return EssayMetrics(
            word_count=0, sentence_count=0, avg_sentence_length=0.0,
            avg_parse_depth=0.0, complex_sentence_ratio=0.0,
            lexical_diversity=0.0,
        )

    avg_sentence_length = word_count / sentence_count
    avg_parse_depth = sum(sentence_depth(s) for s in sentences) / sentence_count
    complex_count = sum(1 for s in sentences if has_subordinate_clause(s))
    unique_words = {t.lemma_.lower() for t in words}

    return EssayMetrics(
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_length=round(avg_sentence_length, 2),
        avg_parse_depth=round(avg_parse_depth, 2),
        complex_sentence_ratio=round(complex_count / sentence_count, 2),
        lexical_diversity=round(len(unique_words) / word_count, 2),
    )