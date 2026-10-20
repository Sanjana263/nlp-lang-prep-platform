"""
SQLAlchemy models for the 11 entities of SRS Table 6.1.

Deliberate additions beyond the SRS (marked "ADDED") - see notes in chat:
  * users.role                    -> FR-1.8 / NFR-2.2 (student vs admin)
  * writing/speaking .status      -> NLP/STT run as background tasks (Sec 5.2.4, NFR-3.2)
  * results.status                -> NFR-3.3 (not complete until all scores exist)
  * unique constraints on DashboardStats / UserVocabularyProgress
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, func, true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

now = func.now()


# ---------------------------------------------------------------- users
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("target_exam IN ('IELTS','TOEFL','PTE')", name="ck_users_target_exam"),
        CheckConstraint("role IN ('student','admin')", name="ck_users_role"),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    target_exam: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20), default="student", server_default="student")  # ADDED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


# ---------------------------------------------------------- content bank
class ReadingPassage(Base):
    __tablename__ = "reading_passages"

    passage_id: Mapped[int] = mapped_column(primary_key=True)
    passage_text: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(String(20))  # Easy / Medium / Hard
    questions_json: Mapped[dict] = mapped_column(JSONB)         # questions + correct answers


class ListeningClip(Base):
    __tablename__ = "listening_clips"

    audio_clip_id: Mapped[int] = mapped_column(primary_key=True)
    audio_file_path: Mapped[str] = mapped_column(String(255))
    accent_type: Mapped[str] = mapped_column(String(20))    # British / American / Australian
    section_type: Mapped[str] = mapped_column(String(30))   # Conversation / Monologue / Lecture
    clip_transcript_text: Mapped[str] = mapped_column(Text)


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"

    word_id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(50), unique=True)
    meaning: Mapped[str] = mapped_column(Text)
    example_sentence: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(String(20))  # Beginner / Intermediate / Advanced


class WritingPrompt(Base):
    """Writing question bank (ADDED: the SRS has no writing-prompt table)."""
    __tablename__ = "writing_prompts"
    __table_args__ = (
        CheckConstraint("writing_type IN ('essay','letter','report','graph_description')", name="ck_writing_prompts_type"),
    )

    prompt_id: Mapped[int] = mapped_column(primary_key=True)
    writing_type: Mapped[str] = mapped_column(String(20), default="essay", server_default="essay", index=True)
    topic: Mapped[str] = mapped_column(String(50))
    question_type: Mapped[str] = mapped_column(String(30))   # opinion / discuss_both / problem_solution / ...
    prompt_text: Mapped[str] = mapped_column(Text, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


# ----------------------------------------------------------- submissions
class WritingSubmission(Base):
    __tablename__ = "writing_submissions"

    writing_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    task_type: Mapped[str] = mapped_column(String(20))
    prompt_text: Mapped[str] = mapped_column(Text)
    submitted_text: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer)
    # scores are nullable: they are filled in after the background NLP task finishes
    task_response_score: Mapped[float | None] = mapped_column(Float)  # ADDED (IELTS 4th criterion)
    grammar_score: Mapped[float | None] = mapped_column(Float)
    coherence_score: Mapped[float | None] = mapped_column(Float)
    vocabulary_score: Mapped[float | None] = mapped_column(Float)
    mistake_patterns_json: Mapped[list | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")  # ADDED
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


class SpeakingSubmission(Base):
    __tablename__ = "speaking_submissions"

    speaking_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    part_number: Mapped[int] = mapped_column(Integer)
    prompt_id: Mapped[str | None] = mapped_column(String(40))          # ADDED: which question
    prompt_text: Mapped[str | None] = mapped_column(Text)             # ADDED
    audio_file_path: Mapped[str] = mapped_column(String(255))
    duration_seconds: Mapped[float | None] = mapped_column(Float)     # ADDED
    transcribed_text: Mapped[str | None] = mapped_column(Text)
    pronunciation_score: Mapped[float | None] = mapped_column(Float)
    fluency_score: Mapped[float | None] = mapped_column(Float)
    pace_score: Mapped[float | None] = mapped_column(Float)            # words per minute
    lexical_score: Mapped[float | None] = mapped_column(Float)         # ADDED (IELTS criterion)
    grammar_score: Mapped[float | None] = mapped_column(Float)         # ADDED (IELTS criterion)
    overall_band: Mapped[float | None] = mapped_column(Float)          # ADDED
    filler_word_count: Mapped[int | None] = mapped_column(Integer)
    mistake_patterns_json: Mapped[list | None] = mapped_column(JSONB)
    analysis_json: Mapped[dict | None] = mapped_column(JSONB)          # ADDED: words, metrics, feedback
    error_message: Mapped[str | None] = mapped_column(Text)            # ADDED: NFR-3.2, shown to the user
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")  # ADDED
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


class ReadingSubmission(Base):
    __tablename__ = "reading_submissions"

    reading_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    passage_id: Mapped[int] = mapped_column(ForeignKey("reading_passages.passage_id"))
    answers_json: Mapped[dict] = mapped_column(JSONB)
    score: Mapped[float | None] = mapped_column(Float)
    mistake_patterns_json: Mapped[list | None] = mapped_column(JSONB)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


class ListeningSubmission(Base):
    __tablename__ = "listening_submissions"

    listening_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    audio_clip_id: Mapped[int] = mapped_column(ForeignKey("listening_clips.audio_clip_id"))
    transcribed_text: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    mistake_patterns_json: Mapped[list | None] = mapped_column(JSONB)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


# ------------------------------------------------------ results & stats
class Result(Base):
    __tablename__ = "results"

    result_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    # optional one-to-one into each submission (a result may cover any subset of skills)
    writing_id: Mapped[int | None] = mapped_column(ForeignKey("writing_submissions.writing_id"), unique=True)
    speaking_id: Mapped[int | None] = mapped_column(ForeignKey("speaking_submissions.speaking_id"), unique=True)
    reading_id: Mapped[int | None] = mapped_column(ForeignKey("reading_submissions.reading_id"), unique=True)
    listening_id: Mapped[int | None] = mapped_column(ForeignKey("listening_submissions.listening_id"), unique=True)
    overall_band_score: Mapped[float | None] = mapped_column(Float)
    feedback_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")  # ADDED
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now)


class DashboardStat(Base):
    __tablename__ = "dashboard_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_area", name="uq_stats_user_skill"),  # ADDED
        CheckConstraint("skill_area IN ('Reading','Writing','Listening','Speaking')", name="ck_stats_skill"),
    )

    stat_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    skill_area: Mapped[str] = mapped_column(String(20))
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now, onupdate=now)


class UserVocabularyProgress(Base):
    __tablename__ = "user_vocabulary_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_vocab_user_word"),  # ADDED
        CheckConstraint("status IN ('new','learning','mastered')", name="ck_vocab_status"),
    )

    progress_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    word_id: Mapped[int] = mapped_column(ForeignKey("vocabulary_words.word_id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="new", server_default="new")
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
