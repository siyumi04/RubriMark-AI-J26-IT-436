import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.rubric import Rubric, RubricCriterion, RubricRejection
from app.schemas.rubric import (
    RubricCreate,
    RubricUpdate,
    RubricOut,
    RubricCriterionOut,
    RubricCriterionCreate,
    RubricValidationResult,
    DynamicWeightOptimizationRequest,
    DynamicWeightOptimizationResponse,
    STANDARD_REJECTION_REASONS,
    RejectRubricRequest,
    RegenerateRubricRequest,
    RubricVersionHistoryItem,
    RubricVersionHistoryOut,
)
from app.services.ai_service import AIService
from app.services.weight_optimizer import DynamicWeightOptimizer

router = APIRouter(prefix="/rubrics", tags=["3-6. Rubric Lifecycle (Generation, Weights, Validation, Approval, Rejection, Regeneration)"])


class GenerateRubricRequest(BaseModel):
    assessment_id: Optional[int] = None
    question: Optional[str] = None
    question_text: Optional[str] = None
    model_answer: Optional[str] = None
    reference_answer: Optional[str] = None
    learning_outcome: Optional[str] = None
    blooms_level: Optional[str] = "Analyze"
    lecturer_guidelines: Optional[str] = None
    max_marks: Optional[float] = None
    title: Optional[str] = None
    course_code: Optional[str] = "IT4360"
    custom_prompt: Optional[str] = None
    generation_mode: Optional[str] = None
    use_rag: Optional[bool] = None
    force_fallback: Optional[bool] = None


class ApproveRubricRequest(BaseModel):
    approved_by: str = "Dr. Lecturer"
    notes: Optional[str] = "Approved for assessment scoring."


def _serialize_rubric(rubric: Rubric) -> dict:
    """Helper to convert Rubric ORM object to RubricOut compatible dict."""
    criteria_out = []
    for c in rubric.criteria:
        try:
            levels = json.loads(c.performance_levels) if c.performance_levels else []
        except Exception:
            levels = []
        criteria_out.append({
            "id": c.id,
            "rubric_id": c.rubric_id,
            "criterion_name": c.criterion_name,
            "description": c.description,
            "weight_percentage": c.weight_percentage,
            "max_marks": c.max_marks,
            "blooms_dimension": c.blooms_dimension,
            "performance_levels": levels,
        })

    try:
        val_msgs = json.loads(rubric.validation_messages) if rubric.validation_messages else []
    except Exception:
        val_msgs = []

    try:
        rej_reasons = json.loads(rubric.rejection_reasons) if rubric.rejection_reasons else []
    except Exception:
        rej_reasons = []

    return {
        "id": rubric.id,
        "assessment_id": rubric.assessment_id,
        "parent_rubric_id": getattr(rubric, "parent_rubric_id", None),
        "title": rubric.title,
        "version": rubric.version,
        "status": rubric.status,
        "validation_status": rubric.validation_status,
        "validation_score": rubric.validation_score,
        "validation_messages": val_msgs,
        "generation_mode": getattr(rubric, "generation_mode", "rule_based") or "rule_based",
        "rag_context_used": getattr(rubric, "rag_context_used", None),
        "is_approved": rubric.is_approved,
        "approval_notes": rubric.approval_notes,
        "approved_by": rubric.approved_by,
        "rejection_reasons": rej_reasons,
        "rejection_feedback": getattr(rubric, "rejection_feedback", None),
        "rejected_at": getattr(rubric, "rejected_at", None),
        "rejected_by": getattr(rubric, "rejected_by", None),
        "created_at": rubric.created_at,
        "updated_at": rubric.updated_at,
        "criteria": criteria_out,
    }


@router.post("/generate", response_model=RubricOut, status_code=status.HTTP_201_CREATED)
def generate_adaptive_rubric(request: GenerateRubricRequest, db: Session = Depends(get_db)):
    """
    Feature 3: Adaptive Rubric Generation (Rule-Based Baseline Prototype).
    Accepts question, model answer, learning outcome, Bloom's level, lecturer guidelines, and maximum marks.
    Applies dynamic weight optimization, allocates marks, validates, and stores rubric with Pending approval status.
    """
    assessment = None
    if request.assessment_id is not None:
        assessment = db.query(Assessment).filter(Assessment.id == request.assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

    # Resolve question parameters
    q_text = request.question or request.question_text or (assessment.question_text if assessment else None)
    if not q_text:
        raise HTTPException(status_code=400, detail="Question text is required to generate a rubric.")

    ref_answer = request.model_answer or request.reference_answer or (assessment.reference_answer if assessment else None)
    blooms_lvl = request.blooms_level or (assessment.blooms_level if assessment else "Analyze")
    lo = request.learning_outcome or (assessment.learning_outcome if assessment else None)
    guidelines = request.lecturer_guidelines or (assessment.lecturer_guidelines if assessment else None)
    m_marks = float(request.max_marks if request.max_marks is not None else (assessment.max_marks if assessment else 100.0))

    # If no existing assessment, register one
    if not assessment:
        auto_title = request.title or f"Assessment: {q_text[:50]}..."
        assessment = Assessment(
            title=auto_title,
            course_code=request.course_code or "IT4360",
            question_text=q_text,
            reference_answer=ref_answer,
            max_marks=m_marks,
            blooms_level=blooms_lvl,
            cognitive_complexity="Medium",
            learning_outcome=lo,
            lecturer_guidelines=guidelines,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
    else:
        # Update any newly provided details on the assessment
        if request.learning_outcome:
            assessment.learning_outcome = request.learning_outcome
        if request.lecturer_guidelines:
            assessment.lecturer_guidelines = request.lecturer_guidelines
        if request.max_marks is not None:
            assessment.max_marks = m_marks
        if request.blooms_level:
            assessment.blooms_level = blooms_lvl
        db.commit()

    # Determine generation strategy
    should_use_rag = request.use_rag
    if should_use_rag is None:
        if request.generation_mode == "ollama_rag":
            should_use_rag = True
        elif request.generation_mode == "rule_based":
            should_use_rag = False
        elif getattr(settings, "ENABLE_MOCK_AI", False):
            should_use_rag = False
        else:
            should_use_rag = True

    should_force_fallback = request.force_fallback
    if should_force_fallback is None:
        if request.generation_mode == "rule_based":
            should_force_fallback = True
        elif request.generation_mode == "ollama_rag":
            should_force_fallback = False
        elif getattr(settings, "ENABLE_MOCK_AI", False) and request.use_rag is not True:
            should_force_fallback = True
        else:
            should_force_fallback = False

    # Generate criteria via Ollama + RAG (with rule-based fallback)
    generation_result = AIService.generate_rubric_with_rag(
        question_text=q_text,
        blooms_level=blooms_lvl,
        reference_answer=ref_answer,
        learning_outcome=lo,
        lecturer_guidelines=guidelines,
        max_marks=m_marks,
        use_rag=should_use_rag,
        force_fallback=should_force_fallback,
    )
    generated_criteria = generation_result["criteria"]
    gen_mode = generation_result.get("generation_mode", "rule_based")
    rag_context_used = generation_result.get("rag_context_used")
    validation = generation_result.get("validation") or AIService.validate_rubric(generated_criteria, max_marks=m_marks)

    # Determine version and parent rubric
    latest_rubric = (
        db.query(Rubric)
        .filter(Rubric.assessment_id == assessment.id)
        .order_by(Rubric.version.desc(), Rubric.id.desc())
        .first()
    )
    new_version = (latest_rubric.version + 1) if (latest_rubric and latest_rubric.version) else 1
    parent_id = latest_rubric.id if latest_rubric else None

    # Persist rubric with PENDING approval status (do not automatically approve)
    rubric = Rubric(
        assessment_id=assessment.id,
        version=new_version,
        parent_rubric_id=parent_id,
        title=f"Adaptive Rubric for {assessment.title} (v{new_version})" if new_version > 1 else f"Adaptive Rubric for {assessment.title}",
        status="pending_approval",
        validation_status=validation["status"],
        validation_score=validation["validation_score"],
        validation_messages=json.dumps(validation["messages"]),
        generation_mode=gen_mode,
        rag_context_used=rag_context_used,
        is_approved=False,
        approval_notes=f"Pending lecturer review and official approval. Generated via {gen_mode}."
    )
    db.add(rubric)
    db.commit()
    db.refresh(rubric)

    # Add criteria
    for crit in generated_criteria:
        c_model = RubricCriterion(
            rubric_id=rubric.id,
            criterion_name=crit["criterion_name"],
            description=crit["description"],
            weight_percentage=crit["weight_percentage"],
            max_marks=crit.get("max_marks", round((crit["weight_percentage"] / 100.0) * m_marks, 2)),
            blooms_dimension=crit.get("blooms_dimension", "Analytical"),
            performance_levels=json.dumps(crit.get("performance_levels", []))
        )
        db.add(c_model)

    db.commit()
    db.refresh(rubric)
    return _serialize_rubric(rubric)


@router.get("/assessment/{assessment_id}", response_model=List[RubricOut])
def get_rubrics_by_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all rubrics associated with an assessment, ordered chronologically by version.
    """
    rubrics = (
        db.query(Rubric)
        .filter(Rubric.assessment_id == assessment_id)
        .order_by(Rubric.version.asc(), Rubric.id.asc())
        .all()
    )
    return [_serialize_rubric(r) for r in rubrics]


@router.get("/{rubric_id}", response_model=RubricOut)
def get_rubric_detail(rubric_id: int, db: Session = Depends(get_db)):
    """
    Gets details of a rubric by ID.
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return _serialize_rubric(rubric)


@router.put("/{rubric_id}", response_model=RubricOut)
def update_rubric(rubric_id: int, update_in: RubricUpdate, db: Session = Depends(get_db)):
    """
    Feature 6: Lecturer Rubric Editing.
    Allows lecturers to edit criteria, weights, and performance level descriptors.
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    if rubric.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot edit an approved rubric directly. Please create or regenerate a new version."
        )
    if rubric.status == "rejected":
        raise HTTPException(
            status_code=400,
            detail="Cannot edit a rejected rubric directly. Please regenerate a new rubric version."
        )

    if update_in.title is not None:
        rubric.title = update_in.title
    if update_in.status is not None:
        rubric.status = update_in.status

    # If criteria are updated, replace them
    if update_in.criteria is not None:
        # Delete existing criteria
        db.query(RubricCriterion).filter(RubricCriterion.rubric_id == rubric.id).delete()
        for crit in update_in.criteria:
            c_model = RubricCriterion(
                rubric_id=rubric.id,
                criterion_name=crit.criterion_name,
                description=crit.description,
                weight_percentage=crit.weight_percentage,
                max_marks=crit.max_marks,
                blooms_dimension=crit.blooms_dimension,
                performance_levels=json.dumps([p.model_dump() for p in (crit.performance_levels or [])])
            )
            db.add(c_model)

        # Re-validate
        assessment = rubric.assessment or (db.query(Assessment).filter(Assessment.id == rubric.assessment_id).first() if rubric.assessment_id else None)
        max_marks = assessment.max_marks if (assessment and assessment.max_marks is not None) else 100.0

        criteria_dicts = [c.model_dump() for c in update_in.criteria]
        validation = AIService.validate_rubric(criteria_dicts, max_marks=max_marks)
        rubric.validation_status = validation["status"]
        rubric.validation_score = validation["validation_score"]
        rubric.validation_messages = json.dumps(validation["messages"])

    db.commit()
    db.refresh(rubric)
    return _serialize_rubric(rubric)


@router.post("/{rubric_id}/optimize-weights", response_model=DynamicWeightOptimizationResponse)
def optimize_rubric_weights(rubric_id: int, db: Session = Depends(get_db)):
    """
    Feature 4: Dynamic Weight Optimization.
    Recalibrates criterion weights to sum to 100% based on Bloom's taxonomy & balance algorithms.
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    if rubric.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot optimize weights for an approved rubric. Please create a new version to modify weights."
        )
    if rubric.status == "rejected":
        raise HTTPException(
            status_code=400,
            detail="Cannot optimize weights for a rejected rubric. Please regenerate a new rubric version."
        )

    assessment = rubric.assessment
    blooms_level = assessment.blooms_level if assessment else "Analyze"

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

    max_marks = assessment.max_marks if assessment else 100.0
    q_text = assessment.question_text if assessment else ""
    lo = assessment.learning_outcome if assessment else ""
    guidelines = assessment.lecturer_guidelines if assessment else ""
    current_weight_sum = sum(float(c.weight_percentage or 0.0) for c in rubric.criteria)
    is_already_optimized = (
        rubric.status == "weights_optimized"
        or (
            rubric.generation_mode in ("rule_based", "rule_based_fallback", "ollama_rag", "ollama_feedback_regenerated")
            and abs(current_weight_sum - 100.0) < 0.1
        )
    )

    result = DynamicWeightOptimizer.optimize_and_allocate(
        criteria=criteria_list,
        max_marks=max_marks,
        target_blooms_level=blooms_level,
        question_text=q_text,
        learning_outcome=lo or "",
        lecturer_guidelines=guidelines or "",
        is_already_optimized=is_already_optimized
    )

    # Update in DB
    for updated_c in result["criteria"]:
        crit_row = db.query(RubricCriterion).filter(RubricCriterion.id == updated_c["id"]).first()
        if crit_row:
            crit_row.weight_percentage = updated_c["weight_percentage"]
            crit_row.max_marks = updated_c.get("max_marks", round((updated_c["weight_percentage"] / 100.0) * max_marks, 2))

    rubric.status = "weights_optimized"
    db.commit()
    db.refresh(rubric)

    return {
        "rubric_id": rubric.id,
        "version": rubric.version,
        "optimized_criteria": result["criteria"],
        "total_weight": result["total_weight"],
        "total_marks": result.get("total_marks", max_marks),
        "optimization_rationale": result["rationale"],
        "status": result["status"]
    }


@router.post("/{rubric_id}/validate", response_model=RubricValidationResult)
def validate_rubric(rubric_id: int, db: Session = Depends(get_db)):
    """
    Feature 5: Rubric Validation.
    Executes automated validation checks (100% weight sum, descriptors completeness, clarity, marks match).
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    assessment = rubric.assessment
    max_marks = assessment.max_marks if assessment else 100.0

    criteria_list = []
    for c in rubric.criteria:
        criteria_list.append({
            "criterion_name": c.criterion_name,
            "weight_percentage": c.weight_percentage,
            "max_marks": c.max_marks,
            "performance_levels": json.loads(c.performance_levels) if c.performance_levels else []
        })

    validation = AIService.validate_rubric(criteria_list, max_marks=max_marks)

    rubric.validation_status = validation["status"]
    rubric.validation_score = validation["validation_score"]
    rubric.validation_messages = json.dumps(validation["messages"])
    db.commit()

    return {
        "rubric_id": rubric.id,
        "is_valid": validation["is_valid"],
        "validation_score": validation["validation_score"],
        "status": validation["status"],
        "checks": validation["checks"],
        "messages": validation["messages"],
        "recommendations": validation["recommendations"]
    }


@router.post("/{rubric_id}/approve", response_model=RubricOut)
def approve_rubric(rubric_id: int, request: ApproveRubricRequest, db: Session = Depends(get_db)):
    """
    Feature 6: Lecturer Rubric Approval.
    Marks a rubric as officially approved and locked for student scoring.
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # A rejected rubric cannot be approved directly; it must be regenerated
    if rubric.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve a rejected rubric. A rejected rubric must be regenerated into a new version before approval."
        )

    rubric.is_approved = True
    rubric.status = "approved"
    rubric.approved_by = request.approved_by
    rubric.approval_notes = request.notes
    db.commit()
    db.refresh(rubric)

    return _serialize_rubric(rubric)


@router.post("/{rubric_id}/reject", response_model=RubricOut)
def reject_rubric(rubric_id: int, request: RejectRubricRequest, db: Session = Depends(get_db)):
    """
    Phase 3 - Requirement 2, 3, 4: Lecturer Rubric Rejection.
    Allows lecturers to reject draft/pending rubrics with one or multiple reasons,
    optional written feedback, and timestamping in SQLite.
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # If rubric is already approved and has student submissions, prevent rejection
    if rubric.is_approved:
        scored_submissions = rubric.assessment.submissions if rubric.assessment else []
        if len(scored_submissions) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject an approved rubric that is actively used for scored student submissions."
            )

    cleaned_reasons = [r.strip() for r in (request.rejection_reasons or []) if r.strip()]
    if not cleaned_reasons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one rejection reason must be selected."
        )

    now = datetime.utcnow()
    rubric.status = "rejected"
    rubric.is_approved = False
    rubric.rejection_reasons = json.dumps(cleaned_reasons)
    rubric.rejection_feedback = request.feedback.strip() if request.feedback else None
    rubric.rejected_at = now
    rubric.rejected_by = request.rejected_by or "Dr. Lecturer"

    rejection_record = RubricRejection(
        rubric_id=rubric.id,
        rejection_reasons=json.dumps(cleaned_reasons),
        feedback=request.feedback.strip() if request.feedback else None,
        rejected_by=request.rejected_by or "Dr. Lecturer",
        created_at=now,
    )
    db.add(rejection_record)
    db.commit()
    db.refresh(rubric)

    return _serialize_rubric(rubric)


@router.post("/{rubric_id}/regenerate", response_model=RubricOut, status_code=status.HTTP_201_CREATED)
def regenerate_feedback_driven_rubric(
    rubric_id: int,
    request: Optional[RegenerateRubricRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Phase 3 - Requirement 5, 6, 7, 8: Feedback-Driven Rubric Regeneration.
    Synthesizes a brand-new rubric version incorporating:
    - Original lecturer assessment inputs
    - Previously generated rubric criteria
    - Lecturer rejection reasons and feedback
    - Retrieved RAG context
    - Ollama llama3.2:1b (with dynamic weight optimization & validation)
    Preserves all previous versions without overwriting.
    """
    if request is None:
        request = RegenerateRubricRequest()

    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    assessment = rubric.assessment
    if not assessment:
        raise HTTPException(status_code=404, detail="Associated assessment not found")

    existing_reasons = []
    if rubric.rejection_reasons:
        try:
            existing_reasons = json.loads(rubric.rejection_reasons)
        except Exception:
            existing_reasons = []

    req_reasons = [r.strip() for r in (request.rejection_reasons or []) if r.strip()]
    active_reasons = req_reasons if req_reasons else existing_reasons
    if not active_reasons:
        active_reasons = ["General Revision Required"]

    active_feedback = request.feedback if request.feedback is not None else rubric.rejection_feedback

    now = datetime.utcnow()
    if rubric.status != "rejected":
        rubric.status = "rejected"
        rubric.is_approved = False
        rubric.rejection_reasons = json.dumps(active_reasons)
        rubric.rejection_feedback = active_feedback
        rubric.rejected_at = now
        rubric.rejected_by = request.rejected_by or rubric.rejected_by or "Dr. Lecturer"

        rejection_record = RubricRejection(
            rubric_id=rubric.id,
            rejection_reasons=json.dumps(active_reasons),
            feedback=active_feedback,
            rejected_by=request.rejected_by or "Dr. Lecturer",
            created_at=now,
        )
        db.add(rejection_record)
        db.commit()

    max_ver = (
        db.query(func.max(Rubric.version))
        .filter(Rubric.assessment_id == assessment.id)
        .scalar()
    ) or rubric.version
    new_version = max_ver + 1

    prev_criteria = []
    for c in rubric.criteria:
        prev_criteria.append({
            "id": c.id,
            "criterion_name": c.criterion_name,
            "description": c.description,
            "weight_percentage": c.weight_percentage,
            "max_marks": c.max_marks,
            "blooms_dimension": c.blooms_dimension,
        })

    q_text = assessment.question_text
    ref_answer = assessment.reference_answer
    blooms_lvl = assessment.blooms_level or "Analyze"
    lo = assessment.learning_outcome
    guidelines = assessment.lecturer_guidelines
    m_marks = float(assessment.max_marks or 100.0)

    should_use_rag = request.use_rag
    if should_use_rag is None:
        if request.generation_mode == "ollama_rag":
            should_use_rag = True
        elif request.generation_mode == "rule_based":
            should_use_rag = False
        elif getattr(settings, "ENABLE_MOCK_AI", False):
            should_use_rag = False
        else:
            should_use_rag = True

    should_force_fallback = request.force_fallback
    if should_force_fallback is None:
        if request.generation_mode == "rule_based":
            should_force_fallback = True
        elif request.generation_mode == "ollama_rag":
            should_force_fallback = False
        elif getattr(settings, "ENABLE_MOCK_AI", False) and request.use_rag is not True:
            should_force_fallback = True
        else:
            should_force_fallback = False

    generation_result = AIService.regenerate_rubric_with_feedback(
        question_text=q_text,
        blooms_level=blooms_lvl,
        reference_answer=ref_answer,
        learning_outcome=lo,
        lecturer_guidelines=guidelines,
        max_marks=m_marks,
        previous_criteria=prev_criteria,
        rejection_reasons=active_reasons,
        rejection_feedback=active_feedback,
        previous_version=rubric.version,
        use_rag=should_use_rag,
        force_fallback=should_force_fallback,
    )

    generated_criteria = generation_result["criteria"]
    gen_mode = generation_result.get("generation_mode", "rule_based_fallback")
    rag_context_used = generation_result.get("rag_context_used")
    validation = generation_result.get("validation") or AIService.validate_rubric(generated_criteria, max_marks=m_marks)

    new_rubric = Rubric(
        assessment_id=assessment.id,
        version=new_version,
        parent_rubric_id=rubric.id,
        title=f"Adaptive Rubric for {assessment.title} (v{new_version})",
        status="pending_approval",
        validation_status=validation["status"],
        validation_score=validation["validation_score"],
        validation_messages=json.dumps(validation["messages"]),
        generation_mode=gen_mode,
        rag_context_used=rag_context_used,
        is_approved=False,
        approval_notes=(
            f"Pending lecturer review and official approval. Regenerated (v{new_version}) "
            f"addressing v{rubric.version} feedback [{', '.join(active_reasons)}] via {gen_mode}."
        )
    )
    db.add(new_rubric)
    db.commit()
    db.refresh(new_rubric)

    for crit in generated_criteria:
        c_model = RubricCriterion(
            rubric_id=new_rubric.id,
            criterion_name=crit["criterion_name"],
            description=crit["description"],
            weight_percentage=crit["weight_percentage"],
            max_marks=crit.get("max_marks", round((crit["weight_percentage"] / 100.0) * m_marks, 2)),
            blooms_dimension=crit.get("blooms_dimension", "Analytical"),
            performance_levels=json.dumps(crit.get("performance_levels", []))
        )
        db.add(c_model)

    db.commit()
    db.refresh(new_rubric)
    return _serialize_rubric(new_rubric)


@router.get("/{rubric_id}/history", response_model=RubricVersionHistoryOut)
def get_rubric_history(rubric_id: int, db: Session = Depends(get_db)):
    """
    Phase 3 - Requirement 10: Rubric Version History.
    Returns complete chronological version history for the rubric's assessment.
    """
    rubric = db.query(Rubric).filter(Rubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    return get_assessment_rubric_history(rubric.assessment_id, db=db, current_rubric_id=rubric.id)


@router.get("/assessment/{assessment_id}/history", response_model=RubricVersionHistoryOut)
def get_assessment_rubric_history(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_rubric_id: Optional[int] = None
):
    """
    Phase 3 - Requirement 10: Assessment Rubrics Version History.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    rubrics = (
        db.query(Rubric)
        .filter(Rubric.assessment_id == assessment_id)
        .order_by(Rubric.version.asc(), Rubric.id.asc())
        .all()
    )

    items = []
    for r in rubrics:
        try:
            reasons = json.loads(r.rejection_reasons) if r.rejection_reasons else []
        except Exception:
            reasons = []

        total_marks = round(sum(float(c.max_marks) for c in r.criteria), 2)
        items.append(RubricVersionHistoryItem(
            id=r.id,
            version=r.version,
            parent_rubric_id=r.parent_rubric_id,
            title=r.title,
            status=r.status,
            is_approved=r.is_approved,
            generation_mode=r.generation_mode or "rule_based",
            validation_status=r.validation_status or "pending",
            validation_score=r.validation_score or 0.0,
            rejection_reasons=reasons,
            rejection_feedback=r.rejection_feedback,
            rejected_at=r.rejected_at,
            rejected_by=r.rejected_by,
            approved_by=r.approved_by,
            created_at=r.created_at,
            criteria_count=len(r.criteria),
            total_marks=total_marks,
        ))

    return RubricVersionHistoryOut(
        assessment_id=assessment_id,
        current_rubric_id=current_rubric_id or (rubrics[-1].id if rubrics else None),
        versions=items
    )
