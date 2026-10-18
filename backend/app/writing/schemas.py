from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class EssayRequest(BaseModel):
    essay: str = Field(..., min_length=50, description="The IELTS essay text")
    task_type: str = Field(default="task2", pattern="^task[12]$", description="task1 or task2")
    prompt_text: str = Field(default="", description="The question the essay answers")


class EssayMetrics(BaseModel):
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    avg_parse_depth: float
    complex_sentence_ratio: float
    lexical_diversity: float


class BandScores(BaseModel):
    task_response: float
    coherence: float
    vocabulary: float
    grammar: float
    overall: float


class EssayResult(BaseModel):
    submission_id: int
    metrics: EssayMetrics
    bands: BandScores
    feedback: List[str]


class WritingSubmissionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    writing_id: int
    task_type: str
    word_count: int
    task_response_score: float | None
    grammar_score: float | None
    coherence_score: float | None
    vocabulary_score: float | None
    status: str
    submitted_at: datetime
