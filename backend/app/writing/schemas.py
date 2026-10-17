from pydantic import BaseModel, Field
from typing import List


class EssayRequest(BaseModel):
    essay: str = Field(..., min_length=50, description="The IELTS essay text")
    task_type: str = Field(default="task2", description="task1 or task2")


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
    metrics: EssayMetrics
    bands: BandScores
    feedback: List[str]