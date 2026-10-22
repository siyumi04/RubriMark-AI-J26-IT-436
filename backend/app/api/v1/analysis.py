from fastapi import APIRouter
from app.schemas.submission import QuestionAnalysisRequest, QuestionAnalysisResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/analysis", tags=["2. AI Question Analysis"])


@router.post("/question", response_model=QuestionAnalysisResponse)
def analyze_question(request: QuestionAnalysisRequest):
    """
    Feature 2: AI Question Analysis.
    Analyzes subjective questions using Bloom's Taxonomy, cognitive complexity estimation,
    and conceptual entity extraction.
    """
    analysis = AIService.analyze_question(
        question_text=request.question_text,
        reference_answer=request.reference_answer,
        learning_outcome=getattr(request, 'learning_outcome', None),
        lecturer_guidelines=getattr(request, 'lecturer_guidelines', None),
    )
    return analysis
