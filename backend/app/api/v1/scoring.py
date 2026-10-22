import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.rubric import Rubric
from app.models.submission import StudentSubmission, CriterionScore
from app.schemas.submission import (
    ScoringEvaluationRequest,
    StudentSubmissionOut,
    CriterionScoreOut,
)
from app.services.ai_service import AIService
from app.services.semantic_evaluator import SemanticScoringService

router = APIRouter(prefix="/scoring", tags=["7. Criterion-Based Student Answer Scoring"])


def _serialize_submission(sub: StudentSubmission) -> dict:
    return {
        "id": sub.id,
        "assessment_id": sub.assessment_id,
        "student_id": sub.student_id,
        "student_name": sub.student_name,
        "answer_text": sub.answer_text,
        "total_score": sub.total_score,
        "max_marks": sub.max_marks,
        "percentage": sub.percentage,
        "status": sub.status,
        "scoring_method": getattr(sub, "scoring_method", "semantic") or "semantic",
        "semantic_engine": getattr(sub, "semantic_engine", "local_semantic_nlp") or "local_semantic_nlp",
        "overall_feedback": sub.overall_feedback,
        "created_at": sub.created_at,
        "criterion_scores": [
            {
                "id": cs.id,
                "criterion_id": cs.criterion_id,
                "criterion_name": cs.criterion_name,
                "score_awarded": cs.score_awarded,
                "max_score": cs.max_score,
                "weight_percentage": cs.weight_percentage,
                "performance_level": cs.performance_level,
                "conceptual_alignment": getattr(cs, "conceptual_alignment", 0.0) or 0.0,
                "evidence_quote": getattr(cs, "evidence_quote", "") or "",
                "feedback": cs.feedback,
                "confidence_score": cs.confidence_score,
            }
            for cs in sub.criterion_scores
        ]
    }


@router.post("/evaluate", response_model=StudentSubmissionOut, status_code=status.HTTP_201_CREATED)
def evaluate_student_answer(request: ScoringEvaluationRequest, db: Session = Depends(get_db)):
    """
    Feature 7: Criterion-Based Student Answer Scoring.
    Evaluates student subjective response against an approved rubric, awarding granular criterion marks,
    evidence-based explanations, and conceptual semantic alignment.
    Supports configurable evaluation methods: 'semantic' (default) and 'keyword_baseline' (baseline comparison).
    """
    assessment = db.query(Assessment).filter(Assessment.id == request.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    rubric = db.query(Rubric).filter(Rubric.id == request.rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # Requirement 9: Enforce that only approved rubrics can be used for official scoring; rejected rubrics are strictly blocked
    if rubric.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot score student submissions with a rejected rubric. A rejected rubric cannot be used for official evaluation."
        )

    if not rubric.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot score student submissions with an unapproved rubric. The rubric must be reviewed and officially approved by a lecturer first."
        )

    # Serialize criteria for scoring
    criteria_list = []
    for c in rubric.criteria:
        criteria_list.append({
            "id": c.id,
            "criterion_name": c.criterion_name,
            "description": c.description,
            "weight_percentage": c.weight_percentage,
            "max_marks": c.max_marks,
            "blooms_dimension": c.blooms_dimension,
            "performance_levels": json.loads(c.performance_levels) if c.performance_levels else []
        })

    ref_answer = getattr(assessment, "reference_answer", None)
    if not ref_answer and hasattr(assessment, "model_answer"):
        ref_answer = assessment.model_answer

    method = (request.scoring_method or "semantic").lower()
    if method == "keyword_baseline":
        scoring_result = SemanticScoringService.evaluate_keyword_baseline(
            answer_text=request.answer_text,
            criteria=criteria_list,
            model_answer=ref_answer
        )
    else:
        # Default to genuine semantic evaluation
        scoring_result = SemanticScoringService.evaluate_semantic(
            answer_text=request.answer_text,
            criteria=criteria_list,
            model_answer=ref_answer,
            question_text=assessment.question_text
        )

    # Save Submission
    sub = StudentSubmission(
        assessment_id=assessment.id,
        student_id=request.student_id,
        student_name=request.student_name,
        answer_text=request.answer_text,
        total_score=scoring_result["total_score"],
        max_marks=scoring_result["max_marks"],
        percentage=scoring_result["percentage"],
        status="scored",
        scoring_method=scoring_result.get("scoring_method", method),
        semantic_engine=scoring_result.get("semantic_engine", "local_semantic_nlp"),
        overall_feedback=scoring_result["overall_feedback"]
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Save Criterion Breakdown with evidence quotes
    for cs in scoring_result["criterion_scores"]:
        cs_row = CriterionScore(
            submission_id=sub.id,
            criterion_id=cs["criterion_id"],
            criterion_name=cs["criterion_name"],
            score_awarded=cs["score_awarded"],
            max_score=cs["max_score"],
            weight_percentage=cs["weight_percentage"],
            performance_level=cs["performance_level"],
            conceptual_alignment=cs.get("conceptual_alignment", 0.0),
            evidence_quote=cs.get("evidence_quote", ""),
            feedback=cs["feedback"],
            confidence_score=cs["confidence_score"]
        )
        db.add(cs_row)

    db.commit()
    db.refresh(sub)
    return _serialize_submission(sub)


@router.get("/assessment/{assessment_id}", response_model=List[StudentSubmissionOut])
def get_submissions_by_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all evaluated student submissions for an assessment.
    """
    submissions = db.query(StudentSubmission).filter(StudentSubmission.assessment_id == assessment_id).all()
    return [_serialize_submission(s) for s in submissions]


@router.get("/submission/{submission_id}", response_model=StudentSubmissionOut)
def get_submission_detail(submission_id: int, db: Session = Depends(get_db)):
    """
    Retrieves detailed criterion evaluation of a specific submission.
    """
    sub = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return _serialize_submission(sub)
