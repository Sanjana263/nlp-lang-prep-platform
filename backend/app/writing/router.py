from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models import User, WritingPrompt, WritingSubmission
from app.writing.analyzer import analyze_essay
from app.writing.checks import run_all_checks, structure_tips
from app.writing.schemas import (
    MIN_WORDS, TASK_OF, EssayRequest, EssayResult, WritingPromptOut, WritingSubmissionSummary, WritingType,
)
from app.writing.scorer import score_essay
from app.writing.vocabulary import find_suggestions, rewrite_text

router = APIRouter(prefix="/writing", tags=["writing"])


@router.get("/prompts", response_model=List[WritingPromptOut])
def prompts(
    writing_type: Optional[WritingType] = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The writing question bank (active questions only), optionally filtered by writing type."""
    query = select(WritingPrompt).where(WritingPrompt.is_active.is_(True))
    if writing_type:
        query = query.where(WritingPrompt.writing_type == writing_type)
    return list(db.scalars(query.order_by(WritingPrompt.prompt_id)))


@router.post("/evaluate", response_model=EssayResult)
def evaluate_essay(
    request: EssayRequest,
    user: User = Depends(get_current_user),  # NFR-2.1: login required
    db: Session = Depends(get_db),
):
    # NFR-3.2: save the submission FIRST so it is never lost if analysis fails.
    submission = WritingSubmission(
        user_id=user.user_id,
        task_type=TASK_OF[request.writing_type],
        prompt_text=request.prompt_text,
        submitted_text=request.essay,
        word_count=len(request.essay.split()),
        status="pending",
    )
    db.add(submission)
    db.commit()

    try:
        min_words = MIN_WORDS[request.writing_type]
        metrics = analyze_essay(request.essay)
        issues = run_all_checks(request.essay)
        word_suggestions = find_suggestions(request.essay)
        improved_text, changes = rewrite_text(request.essay)
        bands, feedback = score_essay(metrics, min_words, len(issues))
        feedback += structure_tips(request.essay, request.writing_type)
        if issues:
            feedback.append(f"We found {len(issues)} mistake{'s' if len(issues) != 1 else ''}; see Mistakes found below.")
        if not feedback:
            feedback.append("Good structure. Keep practising with different topics.")
    except Exception:
        submission.status = "failed"
        db.commit()
        raise

    submission.word_count = metrics.word_count
    submission.task_response_score = bands.task_response
    submission.grammar_score = bands.grammar
    submission.coherence_score = bands.coherence
    submission.vocabulary_score = bands.vocabulary
    submission.mistake_patterns_json = issues  # FR-3.5
    submission.status = "completed"
    db.commit()

    return EssayResult(submission_id=submission.writing_id, writing_type=request.writing_type,
                       min_words=min_words, metrics=metrics, bands=bands, issues=issues,
                       word_suggestions=word_suggestions, improved_text=improved_text,
                       changes=changes, feedback=feedback)


@router.get("/submissions", response_model=List[WritingSubmissionSummary])
def my_submissions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(WritingSubmission)
        .where(WritingSubmission.user_id == user.user_id)
        .order_by(WritingSubmission.submitted_at.desc())
    )
    return list(rows)
