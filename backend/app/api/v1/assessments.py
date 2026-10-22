from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, AssessmentOut

router = APIRouter(prefix="/assessments", tags=["1. Lecturer Assessment Creation"])


@router.post("/", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment(assessment_in: AssessmentCreate, db: Session = Depends(get_db)):
    """
    Feature 1: Lecturer Assessment Creation.
    Registers a new subjective question/assessment in the system.
    """
    ref_answer = assessment_in.reference_answer or assessment_in.model_answer
    assessment = Assessment(
        title=assessment_in.title,
        course_code=assessment_in.course_code,
        question_text=assessment_in.question_text,
        reference_answer=ref_answer,
        max_marks=assessment_in.max_marks,
        blooms_level=assessment_in.blooms_level,
        cognitive_complexity=assessment_in.cognitive_complexity,
        learning_outcome=assessment_in.learning_outcome,
        lecturer_guidelines=assessment_in.lecturer_guidelines,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/", response_model=List[AssessmentOut])
def list_assessments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lists all lecturer assessments with deterministic ordering.
    Canonical benchmark assessments (IDs 47-51) are prioritized first,
    followed by remaining assessments ordered by ID ascending.
    """
    benchmark_order = case(
        (Assessment.id.in_([47, 48, 49, 50, 51]), 0),
        else_=1
    )
    return (
        db.query(Assessment)
        .order_by(benchmark_order, Assessment.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """
    Fetches details of an assessment by ID.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.put("/{assessment_id}", response_model=AssessmentOut)
def update_assessment(assessment_id: int, update_data: AssessmentUpdate, db: Session = Depends(get_db)):
    """
    Updates an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(assessment, field, val)

    db.commit()
    db.refresh(assessment)
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """
    Deletes an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    db.delete(assessment)
    db.commit()
    return None
