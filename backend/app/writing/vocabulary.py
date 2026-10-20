"""Word upgrades: suggestions with meanings, and a safe automatic rewrite.
No AI model needed. Everything here is plain Python."""
import re
from typing import Dict, List, Tuple

# ---------- 1. Upgrade dictionary ----------
# common word -> [(better word, meaning, example), ...]
UPGRADES: Dict[str, List[Tuple[str, str, str]]] = {
    "good": [
        ("beneficial", "having a helpful or positive effect", "Regular exercise is beneficial for mental health."),
        ("excellent", "of very high quality", "She gave an excellent presentation."),
        ("favourable", "likely to help or lead to success", "The weather was favourable for farming."),
    ],
    "bad": [
        ("detrimental", "causing harm or damage", "Smoking is detrimental to health."),
        ("harmful", "likely to cause damage", "Too much screen time can be harmful to children."),
        ("adverse", "negative and unwelcome", "The drug had adverse effects on some patients."),
    ],
    "big": [
        ("substantial", "large in amount or importance", "The new law will have a substantial impact on small businesses."),
        ("significant", "important enough to have a clear effect", "There has been a significant rise in online learning."),
        ("considerable", "fairly large in size, amount or degree", "Studying abroad requires considerable effort."),
    ],
    "important": [
        ("crucial", "extremely important and necessary", "Sleep is crucial for learning."),
        ("vital", "absolutely necessary", "Clean water is vital for health."),
        ("essential", "completely necessary", "Communication skills are essential in any job."),
    ],
    "very": [
        ("extremely", "to a very high degree", "The exam was extremely difficult."),
        ("highly", "to a great degree (used with words like effective or likely)", "Online tutoring is highly effective."),
    ],
    "people": [
        ("individuals", "single persons, seen as separate from a group", "Individuals learn at different speeds."),
        ("members of the public", "ordinary people in a society", "Members of the public should be told about the risks."),
        ("citizens", "people who live in a particular country or town", "Citizens expect good public transport."),
    ],
    "thing": [
        ("aspect", "one part or feature of something", "Cost is one aspect of the decision."),
        ("factor", "something that influences a result", "Income is a key factor in health."),
        ("element", "a basic or necessary part of something", "Trust is an element of every strong team."),
    ],
    "get": [
        ("obtain", "to get something, often with effort", "Students must obtain a visa before they travel."),
        ("acquire", "to gain a skill, object or knowledge", "Children acquire language by listening."),
        ("receive", "to be given something", "Employees receive training in their first week."),
    ],
    "make": [
        ("create", "to cause something new to exist", "Technology creates new job opportunities."),
        ("produce", "to make something, especially in large amounts", "The factory produces thousands of phones a day."),
        ("generate", "to produce energy, money or ideas", "Tourism generates income for local communities."),
    ],
    "use": [
        ("utilise", "to make practical use of something", "Schools should utilise digital tools more effectively."),
        ("employ", "to use a method or skill", "Teachers employ different methods to keep students interested."),
    ],
    "help": [
        ("assist", "to help someone do a task", "Volunteers assist elderly people with shopping."),
        ("support", "to help someone or something succeed", "Parents support their children's education."),
        ("benefit", "to be useful or give an advantage to", "Flexible hours benefit working parents."),
    ],
    "show": [
        ("demonstrate", "to prove or make something clear", "Research demonstrates that sleep improves memory."),
        ("illustrate", "to explain something with examples", "The graph illustrates the rise in internet use."),
        ("indicate", "to point to a fact or suggest it", "The results indicate a clear trend."),
    ],
    "think": [
        ("believe", "to accept something as true", "Many experts believe that exercise improves focus."),
        ("argue", "to give reasons to support an opinion", "Critics argue that homework adds stress."),
        ("consider", "to think about something carefully", "Employers consider experience as well as qualifications."),
    ],
    "say": [
        ("state", "to say something clearly and formally", "The report states that crime has fallen."),
        ("claim", "to say something is true without proof", "Some people claim that games improve concentration."),
    ],
    "give": [
        ("provide", "to supply something that is needed", "Schools provide students with books."),
        ("offer", "to make something available", "Universities offer scholarships to talented students."),
    ],
    "a lot of": [
        ("a great deal of", "a large amount of (things you cannot count)", "A great deal of time is wasted on social media."),
        ("a large number of", "many (things you can count)", "A large number of students prefer online classes."),
        ("numerous", "many", "Numerous studies link sleep to performance."),
    ],
    "many": [
        ("numerous", "many", "Numerous studies support this view."),
        ("a large number of", "many (things you can count)", "A large number of graduates study abroad."),
    ],
    "problem": [
        ("issue", "an important topic or difficulty that people discuss", "Pollution is a serious issue in big cities."),
        ("challenge", "something difficult that tests your ability", "Learning a language is a challenge for adults."),
        ("obstacle", "something that blocks progress", "Cost is a major obstacle to higher education."),
    ],
    "hard": [
        ("challenging", "difficult in a way that tests your skill", "Academic writing is challenging for many students."),
        ("demanding", "needing a lot of effort or skill", "Medicine is a demanding profession."),
    ],
    "difficult": [
        ("challenging", "difficult in a way that tests your skill", "Learning to write well is challenging."),
        ("demanding", "needing a lot of effort or skill", "Teaching is a demanding career."),
    ],
    "easy": [
        ("straightforward", "simple and not complicated", "The application process is straightforward."),
        ("effortless", "needing little or no effort", "Experts make difficult tasks look effortless."),
    ],
    "happy": [
        ("delighted", "extremely pleased", "Students were delighted with their results."),
        ("content", "satisfied with what you have", "Most workers are content with their salary."),
    ],
    "kids": [
        ("children", "young people who are not yet adults", "Children learn quickly through play."),
    ],
    "change": [
        ("alter", "to make something different", "Social media has altered the way we communicate."),
        ("transform", "to change something completely", "The internet has transformed education."),
    ],
    "enough": [
        ("sufficient", "as much as is needed", "Many people do not get sufficient sleep."),
        ("adequate", "good enough for a purpose", "The school has adequate resources."),
    ],
    "cheap": [
        ("affordable", "low enough in price for people to pay", "Affordable housing is a priority."),
        ("inexpensive", "low in price", "Online courses are inexpensive."),
    ],
    "expensive": [
        ("costly", "high in price", "Studying abroad can be costly."),
        ("exorbitant", "much too high in price", "Exorbitant rents force people to leave the city."),
    ],
    "buy": [
        ("purchase", "to buy something (formal)", "Customers purchase most goods online."),
        ("acquire", "to get something by buying or other means", "The company acquired three smaller firms."),
    ],
    "because of": [
        ("owing to", "because of (formal)", "Owing to heavy rain, the match was cancelled."),
        ("due to", "caused by", "The delay was due to a technical fault."),
    ],
    "for example": [
        ("for instance", "as an example", "Some jobs, for instance nursing, need strong people skills."),
        ("such as", "used to introduce examples", "Skills such as teamwork are valued by employers."),
    ],
}

# other forms of a word -> the base word used in UPGRADES
FORMS = {
    "gets": "get", "got": "get", "getting": "get",
    "makes": "make", "made": "make", "making": "make",
    "uses": "use", "using": "use", "used": "use",
    "helps": "help", "helped": "help", "helping": "help",
    "shows": "show", "showed": "show", "shown": "show",
    "thinks": "think",
    "says": "say", "said": "say",
    "gives": "give", "gave": "give", "giving": "give",
    "buys": "buy", "bought": "buy", "buying": "buy",
    "problems": "problem", "things": "thing",
    "changes": "change", "changed": "change", "changing": "change",
}


def find_suggestions(text: str, max_items: int = 10) -> List[dict]:
    """Find common words the learner used and list stronger alternatives."""
    lower = text.lower()
    found: Dict[str, dict] = {}

    def record(key: str, offset: int) -> None:
        item = found.setdefault(key, {"count": 0, "offset": offset})
        item["count"] += 1

    for key in (k for k in UPGRADES if " " in k):
        for m in re.finditer(r"\b" + re.escape(key) + r"\b", lower):
            record(key, m.start())
    for m in re.finditer(r"[a-z]+", lower):
        word = FORMS.get(m.group(0), m.group(0))
        if m.group(0) == "used" and lower[m.end():m.end() + 3] == " to":
            continue  # "used to" is not the verb "use"
        if word in UPGRADES and " " not in word:
            record(word, m.start())

    ranked = sorted(found.items(), key=lambda kv: (-kv[1]["count"], kv[1]["offset"]))[:max_items]
    return [
        {
            "word": key,
            "count": info["count"],
            "line": lower.count("\n", 0, info["offset"]) + 1,
            "alternatives": [{"word": w, "meaning": mean, "example": ex} for w, mean, ex in UPGRADES[key]],
        }
        for key, info in ranked
    ]


# ---------- 2. Safe automatic rewrite ----------
# Only swaps that keep the grammar correct. Anything risky stays as the
# learner wrote it (it still appears in the suggestions above).
def _match_case(original: str, new: str) -> str:
    return new[:1].upper() + new[1:] if original[:1].isupper() else new


def _cycler(*options: str):
    """Give the options one by one, so one word is not repeated everywhere."""
    state = {"i": 0}

    def nxt() -> str:
        choice = options[state["i"] % len(options)]
        state["i"] += 1
        return choice

    return nxt


def _article_for(word: str) -> str:
    w = word.lower()
    if w.startswith(("uni", "use", "util", "eu", "one")):
        return "a"
    if w.startswith(("hour", "honest", "honour", "heir")) or w[0] in "aeiou":
        return "an"
    return "a"


def _build_rules():
    rules = []

    def add(pattern: str, fn) -> None:
        rules.append((re.compile(pattern, re.IGNORECASE | re.MULTILINE), fn))

    # very / really / extremely + adjective  ->  one strong adjective
    very_map = {
        "important": _cycler("crucial", "vital", "essential"),
        "good": _cycler("excellent", "outstanding"),
        "bad": _cycler("terrible", "dreadful"),
        "big": _cycler("enormous", "immense"),
        "large": _cycler("vast", "immense"),
        "small": _cycler("tiny", "minuscule"),
        "difficult": _cycler("arduous", "demanding"),
        "happy": _cycler("delighted", "overjoyed"),
        "tired": _cycler("exhausted"),
        "useful": _cycler("invaluable"),
        "interesting": _cycler("fascinating"),
        "beautiful": _cycler("stunning"),
        "cold": _cycler("freezing"),
        "hot": _cycler("scorching"),
        "dangerous": _cycler("hazardous"),
        "expensive": _cycler("costly"),
        "angry": _cycler("furious"),
        "serious": _cycler("grave"),
        "common": _cycler("widespread"),
        "famous": _cycler("renowned"),
        "necessary": _cycler("indispensable"),
        "easy": _cycler("straightforward"),
        "surprised": _cycler("astonished"),
        "afraid": _cycler("terrified"),
    }
    add(r"\b(?:very|really|extremely)\s+(" + "|".join(very_map) + r")\b(?!\s+of\b)",
        lambda m: _match_case(m.group(0), very_map[m.group(1).lower()]()))

    # think / show / get better
    add(r"\bthinks?\s+that\b",
        lambda m: _match_case(m.group(0), "believes that" if m.group(0).lower().startswith("thinks") else "believe that"))
    add(r"\bI think\b(?!\s+(?:about|of)\b)", lambda m: "I believe")
    show_map = {"show": "demonstrate", "shows": "demonstrates", "showed": "demonstrated", "shown": "demonstrated"}
    add(r"\b(show|shows|showed|shown)\s+(that|how|why|what)\b",
        lambda m: _match_case(m.group(0), show_map[m.group(1).lower()] + " " + m.group(2)))
    better = {"get": "improve", "gets": "improves", "got": "improved", "getting": "improving"}
    worse = {"get": "deteriorate", "gets": "deteriorates", "got": "deteriorated", "getting": "deteriorating"}
    add(r"\b(get|gets|got|getting)\s+(better|worse)\b(?!\s+at\b)",
        lambda m: _match_case(m.group(0), (better if m.group(2).lower() == "better" else worse)[m.group(1).lower()]))

    # good / bad / big + the nouns they normally go with
    harm_noun = _cycler("harmful", "detrimental")
    add(r"\bbad\s+(effects?|impact|influence|consequences|habits)\b",
        lambda m: _match_case(m.group(0), harm_noun() + " " + m.group(1)))
    harm_to = _cycler("harmful to", "detrimental to")
    add(r"\bbad for\b", lambda m: _match_case(m.group(0), harm_to()))
    add(r"\bgood\s+(effects?|impact|influence|results?)\b",
        lambda m: _match_case(m.group(0), "positive " + m.group(1)))
    add(r"\bgood for\b", lambda m: _match_case(m.group(0), "beneficial for"))
    add(r"\bgood (ways?)\b", lambda m: _match_case(m.group(0), "effective " + m.group(1)))
    add(r"\bgood idea\b", lambda m: _match_case(m.group(0), "sound idea"))
    add(r"\bgood (opportunit(?:y|ies))\b", lambda m: _match_case(m.group(0), "excellent " + m.group(1)))
    add(r"\bgood chance\b", lambda m: _match_case(m.group(0), "strong chance"))
    big_noun = _cycler("significant", "substantial", "considerable")
    add(r"\bbig\s+(problems?|differences?|impact|changes?|roles?|challenges?|issues?|increases?|effects?|risks?|advantages?|benefits?|numbers?)\b",
        lambda m: _match_case(m.group(0), big_noun() + " " + m.group(1)))

    # single words that are safe to swap
    imp = _cycler("crucial", "vital", "essential")
    add(r"\bimportant\b", lambda m: _match_case(m.group(0), imp()))
    add(r"\bdifficult\b", lambda m: _match_case(m.group(0), "challenging"))
    add(r"\bexpensive\b", lambda m: _match_case(m.group(0), "costly"))
    add(r"\bcheap\b", lambda m: _match_case(m.group(0), "affordable"))
    add(r"\bkids\b", lambda m: _match_case(m.group(0), "children"))
    add(r"\bkid\b", lambda m: _match_case(m.group(0), "child"))
    buy_map = {"buy": "purchase", "buys": "purchases", "bought": "purchased", "buying": "purchasing"}
    add(r"\b(buy|buys|bought|buying)\b", lambda m: _match_case(m.group(0), buy_map[m.group(1).lower()]))
    add(r"\benough\s+(money|time|evidence|food|resources|information|people|skills|space|funds)\b",
        lambda m: _match_case(m.group(0), "sufficient " + m.group(1)))
    many = _cycler("numerous", "a large number of")
    add(r"(?<!how )(?<!too )(?<!so )(?<!as )(?<!not )(?<!very )\bmany\b(?=\s+(?:[a-z]+s|people|children|men|women)\b)",
        lambda m: _match_case(m.group(0), many()))
    because = _cycler("owing to", "due to")
    add(r"\bbecause of\b", lambda m: _match_case(m.group(0), because()))
    add(r"\bfor example\b", lambda m: _match_case(m.group(0), "for instance"))

    # linking words at the start of a sentence
    start = r"(?:(?<=[.!?] )|^)"
    adding = _cycler("Moreover, ", "Furthermore, ", "In addition, ")
    add(start + r"also,?\s+", lambda m: adding())
    add(start + r"but,?\s+(?!however\b)", lambda m: "However, ")
    add(start + r"so,?\s+(?!far\b|many\b|much\b|that\b|long\b|on\b|to\b)", lambda m: "Therefore, ")
    return rules


def rewrite_text(text: str) -> Tuple[str, List[str]]:
    """Return (improved text, list of changes made)."""
    changes: List[str] = []
    inserted = set()
    for pattern, fn in _build_rules():
        def sub(m, fn=fn):
            new = fn(m)
            changes.append(f"{m.group(0).strip()} -> {new.strip()}")
            inserted.update(re.findall(r"[a-z]+", new.lower()))
            return new

        text = pattern.sub(sub, text)

    # fix a / an in front of the words we inserted ("a essential" -> "an essential")
    if inserted:
        article = re.compile(r"\b(a|an)(\s+)(" + "|".join(sorted(inserted, key=len, reverse=True)) + r")\b",
                             re.IGNORECASE)

        def fix(m):
            right = _article_for(m.group(3))
            if m.group(1)[0].isupper():
                right = right.capitalize()
            return right + m.group(2) + m.group(3)

        text = article.sub(fix, text)
    return text, changes