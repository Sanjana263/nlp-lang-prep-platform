from fastapi import APIRouter
from app.writing.schemas import EssayRequest, EssayResult, MIN_WORDS
from app.writing.analyzer import analyze_essay
from app.writing.scorer import score_essay
from app.writing.checks import run_all_checks, structure_tips
from app.writing.vocabulary import find_suggestions, rewrite_text

router = APIRouter(prefix="/writing", tags=["writing"])


@router.post("/evaluate", response_model=EssayResult)
def evaluate_essay(request: EssayRequest):
    min_words = MIN_WORDS[request.writing_type]
    metrics = analyze_essay(request.essay)
    issues = run_all_checks(request.essay)
    word_suggestions = find_suggestions(request.essay)
    improved_text, changes = rewrite_text(request.essay)
    bands, feedback = score_essay(metrics, min_words, len(issues))
    feedback += structure_tips(request.essay, request.writing_type)
    if issues:
        feedback.append(f"{len(issues)} mistake(s) found. See the 'issues' list.")
    if not feedback:
        feedback.append("Good structure. Keep practising with different topics.")
    return EssayResult(writing_type=request.writing_type, min_words=min_words,
                       metrics=metrics, bands=bands, issues=issues,
                       word_suggestions=word_suggestions, improved_text=improved_text,
                       changes=changes, feedback=feedback)