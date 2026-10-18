from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models import User, WritingSubmission
from app.writing.analyzer import analyze_essay
from app.writing.schemas import EssayRequest, EssayResult, WritingSubmissionSummary
from app.writing.scorer import score_essay

router = APIRouter(prefix="/writing", tags=["writing"])


@router.post("/evaluate", response_model=EssayResult)
def evaluate_essay(
    request: EssayRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # NFR-3.2: save the submission FIRST so it is never lost if analysis fails.
    submission = WritingSubmission(
        user_id=user.user_id,
        task_type=request.task_type,
        prompt_text=request.prompt_text,
        submitted_text=request.essay,
        word_count=len(request.essay.split()),
        status="pending",
    )
    db.add(submission)
    db.commit()

    try:
        metrics = analyze_essay(request.essay)
        bands, feedback = score_essay(metrics)
    except Exception:
        submission.status = "failed"
        db.commit()
        raise

    submission.word_count = metrics.word_count
    submission.task_response_score = bands.task_response
    submission.grammar_score = bands.grammar
    submission.coherence_score = bands.coherence
    submission.vocabulary_score = bands.vocabulary
    submission.mistake_patterns_json = []  # FR-3.5: filled in once error detection exists
    submission.status = "completed"
    db.commit()

    return EssayResult(submission_id=submission.writing_id, metrics=metrics, bands=bands, feedback=feedback)


@router.get("/submissions", response_model=List[WritingSubmissionSummary])
def my_submissions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(WritingSubmission)
        .where(WritingSubmission.user_id == user.user_id)
        .order_by(WritingSubmission.submitted_at.desc())
    )
    return list(rows)
