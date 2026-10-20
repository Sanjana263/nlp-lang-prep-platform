"""Rule-based writing checks: no AI model needed, just patterns."""
import re
from typing import Dict, List

Issue = Dict[str, object]


def _issue(text: str, offset: int, kind: str, found: str, message: str) -> Issue:
    line = text.count("\n", 0, offset) + 1
    return {"type": kind, "line": line, "text": found.strip(), "message": message}


# ---------- 1. Repeated words ("the the") ----------
ALLOWED_REPEATS = {"had", "that"}  # "had had" and "that that" can be correct


def check_repeated_words(text: str) -> List[Issue]:
    issues = []
    for m in re.finditer(r"\b([A-Za-z']+)\s+\1\b", text, flags=re.IGNORECASE):
        if m.group(1).lower() in ALLOWED_REPEATS:
            continue
        issues.append(_issue(text, m.start(), "repeated_word", m.group(0),
                             f"The word '{m.group(1)}' is repeated. Remove one."))
    return issues


# ---------- 2. Capitalization ----------
NOT_SENTENCE_END = {"g", "e", "etc", "vs", "dr", "mr", "mrs", "ms", "approx"}


def check_capitalization(text: str) -> List[Issue]:
    issues = []
    # the pronoun "I" written as small "i"
    for m in re.finditer(r"\bi\b(?!\.)", text):
        issues.append(_issue(text, m.start(), "capitalization", m.group(0),
                             "The pronoun 'I' must always be a capital letter."))
    # first letter of the whole text
    m = re.match(r"\s*([a-z])", text)
    if m:
        issues.append(_issue(text, m.start(1), "capitalization", m.group(1),
                             "A sentence must start with a capital letter."))
    # first letter after . ! ?
    for m in re.finditer(r"([.!?])\s+([a-z])", text):
        before = re.search(r"([A-Za-z]+)$", text[:m.start(1)])
        if m.group(1) == "." and before and before.group(1).lower() in NOT_SENTENCE_END:
            continue  # e.g. "e.g. the", "Dr. smith"
        if re.match(r"i(?![A-Za-z])", text[m.start(2):]):
            continue  # a lone "i" is already reported by the pronoun rule
        issues.append(_issue(text, m.start(2), "capitalization", m.group(0),
                             "A new sentence must start with a capital letter."))
    return issues


# ---------- 3. Commonly confused words ----------
CONFUSED_RULES = [
    (r"\btheir\s+(is|are|was|were|has|have|been)\b",
     "'their' shows ownership. Did you mean 'there' (there is / there are)?"),
    (r"\bthere\s+(own|opinions?|parents|friends|children|students|teachers|country|lives?|future|families|family|choices?)\b",
     "Did you mean 'their' (ownership) instead of 'there'?"),
    (r"\bits\s+(a|an|the|not|been|very|also|important|possible|clear|true|necessary|difficult|easy|hard)\b",
     "Did you mean \"it's\" (it is / it has)?"),
    (r"\bit's\s+(own|purpose|effects?|impact|benefits|value|users|aim|goal|role|importance)\b",
     "\"it's\" means 'it is'. For ownership use 'its'."),
    (r"\b(the|an|a|positive|negative|major|great|strong|harmful|significant|serious|bad|good|big|huge|long-term)\s+affect\b",
     "As a noun use 'effect' (the effect of...). 'Affect' is the verb."),
    (r"\b(can|will|may|might|would|could|does|do|to|not)\s+effect\s+(the|their|our|his|her|my|your|students|people|society|children|health|education)\b",
     "When you mean 'influence', the verb is 'affect'."),
    (r"\b(more|less|better|worse|rather|higher|lower|bigger|smaller|larger|greater|fewer|other)\s+then\b",
     "For comparison use 'than', not 'then'."),
    (r"\b(should|could|would|must|might)\s+of\b",
     "Use 'have', not 'of' (should have)."),
    (r"\bto\s+much\b", "Did you mean 'too much'?"),
    (r"\balot\b", "'a lot' is two words."),
    (r"\bloose\s+(weight|money|their|his|her|control|focus|interest)\b",
     "Did you mean 'lose' (verb)? 'Loose' means not tight."),
    (r"\bless\s+(people|students|children|books|mistakes|errors|jobs|cars)\b",
     "Use 'fewer' with things you can count."),
]


def check_confused_words(text: str) -> List[Issue]:
    issues = []
    for pattern, message in CONFUSED_RULES:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            issues.append(_issue(text, m.start(), "confused_word", m.group(0), message))
    return issues


# ---------- 4. Punctuation (every line) ----------
def check_punctuation(text: str) -> List[Issue]:
    issues = []
    for m in re.finditer(r"[ \t]+([,.;:!?])", text):
        issues.append(_issue(text, m.start(), "punctuation", m.group(0) + "...",
                             f"Remove the space before '{m.group(1)}'."))
    for m in re.finditer(r",(?=[A-Za-z])", text):
        issues.append(_issue(text, m.start(), "punctuation", text[max(0, m.start() - 8):m.end() + 8],
                             "Add a space after the comma."))
    for m in re.finditer(r"[a-z]{2,}\.(?=[A-Z])", text):
        issues.append(_issue(text, m.start(), "punctuation", m.group(0),
                             "Add a space after the full stop."))
    for m in re.finditer(r",,|;;|[!?]{2,}|(?<!\.)\.\.(?!\.)", text):
        issues.append(_issue(text, m.start(), "punctuation", m.group(0),
                             "Repeated punctuation. Use only one."))
    # every line: a full line should end with . ! ? or :
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if len(stripped.split()) > 6 and stripped[-1] not in ".!?:\"')":
            issues.append(_issue(text, offset, "punctuation", "..." + stripped[-25:],
                                 "This line does not end with . ! or ?  Add the closing punctuation."))
        offset += len(line)
    return issues


def run_all_checks(text: str) -> List[Issue]:
    issues = (check_repeated_words(text) + check_capitalization(text)
              + check_confused_words(text) + check_punctuation(text))
    return sorted(issues, key=lambda i: i["line"])


# ---------- 5. Tips that depend on the writing type ----------
TREND_WORDS = r"increas|decreas|rise|rose|fall|fell|peak|fluctuat|remain|stable|grow|grew|declin|drop|doubl|reach"


def structure_tips(text: str, writing_type: str) -> List[str]:
    tips = []
    if writing_type == "letter":
        if not re.match(r"\s*(dear|hi|hello)\b", text, flags=re.IGNORECASE):
            tips.append("A letter should start with a greeting such as 'Dear Sir or Madam,'.")
        if not re.search(r"(yours\s+(sincerely|faithfully)|kind regards|best wishes|best regards|sincerely|regards)",
                         text[-120:], flags=re.IGNORECASE):
            tips.append("A letter should end with a sign-off such as 'Yours faithfully,' and your name.")
    elif writing_type == "graph_description":
        if not re.search(r"\d", text):
            tips.append("Include figures from the graph (numbers or percentages) to support your points.")
        if not re.search(TREND_WORDS, text, flags=re.IGNORECASE):
            tips.append("Describe trends with words like 'increased', 'fell', 'remained stable', 'peaked'.")
    elif writing_type == "report":
        if not re.search(r"introduction|summary|overview|conclusion|recommend", text, flags=re.IGNORECASE):
            tips.append("A report needs clear sections: an introduction, findings and a conclusion or recommendation.")
    elif writing_type == "essay":
        if not re.search(r"in conclusion|to conclude|to sum up|in summary|overall", text, flags=re.IGNORECASE):
            tips.append("Finish your essay with a short conclusion ('In conclusion, ...').")
    return tips