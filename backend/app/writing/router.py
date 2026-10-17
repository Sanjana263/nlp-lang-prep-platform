from fastapi import APIRouter
from app.writing.schemas import EssayRequest, EssayResult
from app.writing.analyzer import analyze_essay
from app.writing.scorer import score_essay

router = APIRouter(prefix="/writing", tags=["writing"])


@router.post("/evaluate", response_model=EssayResult)
def evaluate_essay(request: EssayRequest):
    metrics = analyze_essay(request.essay)
    bands, feedback = score_essay(metrics)
    return EssayResult(metrics=metrics, bands=bands, feedback=feedback)