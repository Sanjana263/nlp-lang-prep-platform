"""Optional LLM examiner: refines the text-based criteria and writes examiner-style feedback.

Only used when ANTHROPIC_API_KEY is set. Any failure falls back to the rule-based result,
so the platform never depends on it.
"""
import json
import logging

from pydantic import BaseModel, Field

from app.core.config import get_settings

log = logging.getLogger(__name__)


class Correction(BaseModel):
    original: str = Field(description="The learner's words, quoted exactly from the transcript")
    corrected: str
    explanation: str = Field(description="One short sentence, in plain English")


class ExaminerReview(BaseModel):
    lexical_band: float = Field(description="IELTS Lexical Resource band, 1-9 in steps of 0.5")
    grammar_band: float = Field(description="IELTS Grammatical Range and Accuracy band, 1-9 in steps of 0.5")
    corrections: list[Correction] = Field(description="Up to 5 of the most important grammar or word-choice errors")
    better_vocabulary: list[str] = Field(description="Up to 4 suggestions like 'very big → enormous'")
    feedback: list[str] = Field(description="2-4 specific, encouraging tips, second person, plain English")


SYSTEM = """You are an experienced IELTS Speaking examiner giving practice feedback to a learner.
You receive a verbatim transcript (fillers such as [um] are kept) and measurements already taken
from the audio. Judge only Lexical Resource and Grammatical Range and Accuracy, using the public
IELTS band descriptors. Do not judge pronunciation or fluency: you cannot hear the recording.
Speech transcripts lack written punctuation, so do not penalise punctuation or capitalisation.
Quote corrections exactly from the transcript. Write for a learner: short, kind, concrete."""


def review(question: str, part: int, transcript: str, measured: dict) -> ExaminerReview | None:
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY or not transcript.strip():
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=90.0)
        response = client.beta.messages.create(
            model=settings.FEEDBACK_MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": _schema()},
            },
            system=SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"IELTS Speaking Part {part}. Question: {question}\n\n"
                    f"Transcript:\n{transcript}\n\n"
                    f"Measurements from the audio and text (for context):\n{json.dumps(measured, indent=2)}"
                ),
            }],
        )
        if response.stop_reason == "refusal":
            log.warning("Examiner review refused: %s", getattr(response, "stop_details", None))
            return None
        text = next(b.text for b in response.content if b.type == "text")
        result = ExaminerReview.model_validate_json(text)
        result.lexical_band = _clamp(result.lexical_band)
        result.grammar_band = _clamp(result.grammar_band)
        return result
    except Exception:  # network, auth, rate limit, schema: all fall back to rule-based scoring
        log.exception("Examiner review failed; using rule-based feedback")
        return None


def _clamp(b: float) -> float:
    return max(1.0, min(9.0, round(b * 2) / 2))


def _schema() -> dict:
    """JSON schema for structured output (additionalProperties must be false on every object)."""
    schema = ExaminerReview.model_json_schema()

    def strict(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for v in node.values():
                strict(v)
        elif isinstance(node, list):
            for v in node:
                strict(v)
        return node

    return strict(schema)
