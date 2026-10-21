import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import SpeakingSubmission, User
from app.speaking.prompts import BY_ID, PROMPTS
from app.speaking.schemas import SpeakingPrompt, SpeakingSubmissionDetail, SpeakingSubmissionSummary
from app.speaking.service import process_submission, upload_root

router = APIRouter(prefix="/speaking", tags=["speaking"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
STUCK_AFTER = timedelta(minutes=3)  # a recording still unscored after this long may be retried
AUDIO_TYPES = {"audio/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".m4a", "audio/mpeg": ".mp3",
               "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/wave": ".wav", "video/webm": ".webm"}


def _own(db: Session, user: User, speaking_id: int) -> SpeakingSubmission:
    sub = db.get(SpeakingSubmission, speaking_id)
    if sub is None or sub.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Recording not found")
    return sub


@router.get("/prompts", response_model=List[SpeakingPrompt])
def prompts(_: User = Depends(get_current_user)):
    return PROMPTS


@router.post("/submissions", response_model=SpeakingSubmissionSummary, status_code=status.HTTP_202_ACCEPTED)
async def submit(
    background: BackgroundTasks,
    prompt_id: str = Form(...),
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-5.1-5.2: save the recording, then score it in the background (FR-5.3-5.5)."""
    prompt = BY_ID.get(prompt_id)
    if prompt is None:
        raise HTTPException(status_code=422, detail="Unknown question")
    content_type = (audio.content_type or "").split(";")[0].strip().lower()
    if content_type not in AUDIO_TYPES:
        raise HTTPException(status_code=415, detail="Upload an audio recording (webm, ogg, m4a, mp3 or wav).")
    data = await audio.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The recording is too large. Keep answers under 3 minutes.")
    if len(data) < 1000:
        raise HTTPException(status_code=422, detail="The recording is empty. Check your microphone and try again.")

    settings = get_settings()
    relative = f"speaking/{user.user_id}/{uuid.uuid4().hex}{AUDIO_TYPES[content_type]}"
    path = upload_root(settings.UPLOAD_DIR) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    sub = SpeakingSubmission(
        user_id=user.user_id,
        part_number=prompt["part"],
        prompt_id=prompt_id,
        prompt_text=prompt["question"],
        audio_file_path=relative,
        status="pending",
    )
    db.add(sub)
    db.commit()
    background.add_task(process_submission, sub.speaking_id, settings.UPLOAD_DIR)
    return sub


@router.get("/submissions", response_model=List[SpeakingSubmissionSummary])
def my_submissions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list(db.scalars(
        select(SpeakingSubmission)
        .where(SpeakingSubmission.user_id == user.user_id)
        .order_by(SpeakingSubmission.submitted_at.desc(), SpeakingSubmission.speaking_id.desc())
    ))


@router.get("/submissions/{speaking_id}", response_model=SpeakingSubmissionDetail)
def submission(speaking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """FR-6.3: the learner's own result, with transcript, scores and mistake patterns."""
    return _own(db, user, speaking_id)


@router.get("/submissions/{speaking_id}/audio")
def submission_audio(speaking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = _own(db, user, speaking_id)
    path = upload_root(get_settings().UPLOAD_DIR) / sub.audio_file_path
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Recording file not found")
    return FileResponse(path)


@router.post("/submissions/{speaking_id}/retry", response_model=SpeakingSubmissionSummary, status_code=status.HTTP_202_ACCEPTED)
def retry(speaking_id: int, background: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """NFR-3.2: a failed analysis keeps the recording, so it can be scored again."""
    sub = _own(db, user, speaking_id)
    stuck = sub.status in ("pending", "processing") and datetime.now(timezone.utc) - sub.submitted_at > STUCK_AFTER
    if sub.status != "failed" and not stuck:
        raise HTTPException(status_code=409, detail="Only a recording that failed to score, or is stuck, can be retried.")
    sub.status, sub.error_message = "pending", None
    db.commit()
    background.add_task(process_submission, sub.speaking_id, get_settings().UPLOAD_DIR)
    return sub
