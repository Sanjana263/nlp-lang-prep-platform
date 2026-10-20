from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field

WritingType = Literal["essay", "letter", "report", "graph_description"]

# Minimum words IELTS expects for each writing type
MIN_WORDS: Dict[str, int] = {
    "essay": 250,
    "letter": 150,
    "report": 150,
    "graph_description": 150,
}

# Shortest text we accept for scoring. This is NOT the scoring benchmark: Task Response is still
# judged against MIN_WORDS above, so a 50-word answer is accepted but scores low on length.
SUBMIT_MIN_WORDS: Dict[str, int] = {
    "essay": 50,
    "letter": 50,
    "report": 50,
    "graph_description": 50,
}

# IELTS Task 1 is a letter (General) or a report / graph description (Academic); Task 2 is an essay.
TASK_OF: Dict[str, str] = {"essay": "task2", "letter": "task1", "report": "task1", "graph_description": "task1"}


class EssayRequest(BaseModel):
    essay: str = Field(..., min_length=50, description="The text written by the learner")
    writing_type: WritingType = Field(default="essay", description="essay, letter, report or graph_description")
    prompt_text: str = Field(default="", description="The question the text answers")


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


class Alternative(BaseModel):
    word: str      # the better word
    meaning: str   # what it means
    example: str   # an example sentence


class WordSuggestion(BaseModel):
    word: str                      # the common word the learner used
    count: int                     # how many times it was used
    line: int                      # line of the first use
    alternatives: List[Alternative]


class EssayResult(BaseModel):
    submission_id: int
    writing_type: str
    min_words: int
    metrics: EssayMetrics
    bands: BandScores
    issues: List[Issue]
    word_suggestions: List[WordSuggestion]
    improved_text: str
    changes: List[str]
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


class WritingPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prompt_id: int
    writing_type: str
    topic: str
    question_type: str
    prompt_text: str
