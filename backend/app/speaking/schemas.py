from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SpeakingPrompt(BaseModel):
    id: str
    part: int
    topic: str
    question: str
    points: list[str]
    speak_seconds: int


class SpeakingSubmissionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    speaking_id: int
    part_number: int
    prompt_id: str | None
    prompt_text: str | None
    duration_seconds: float | None
    fluency_score: float | None
    lexical_score: float | None
    grammar_score: float | None
    pronunciation_score: float | None
    overall_band: float | None
    pace_score: float | None
    filler_word_count: int | None
    status: str
    error_message: str | None
    submitted_at: datetime


class SpeakingSubmissionDetail(SpeakingSubmissionSummary):
    transcribed_text: str | None
    mistake_patterns_json: list | None
    analysis_json: dict | None
