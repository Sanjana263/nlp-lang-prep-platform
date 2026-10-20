from pydantic import BaseModel, Field
from typing import Dict, List, Literal

WritingType = Literal["essay", "letter", "report", "graph_description"]

# Minimum words IELTS expects for each writing type
MIN_WORDS: Dict[str, int] = {
    "essay": 250,
    "letter": 150,
    "report": 150,
    "graph_description": 150,
}


class EssayRequest(BaseModel):
    essay: str = Field(..., min_length=50, description="The text written by the learner")
    writing_type: WritingType = Field(default="essay", description="essay, letter, report or graph_description")


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


class Issue(BaseModel):
    type: str      # repeated_word, capitalization, confused_word, punctuation
    line: int      # line number in the learner's text
    text: str      # the part of the text that has the problem
    message: str   # what is wrong and how to fix it


class EssayResult(BaseModel):
    writing_type: str
    min_words: int
    metrics: EssayMetrics
    bands: BandScores
    issues: List[Issue]
    feedback: List[str]