import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import Student, Question, StudentAnswer, Feedback, LearningRecommendation
from app.schemas.schemas import (
    HealthResponse,
    StudentResponse,
    QuestionResponse,
    StudentAnswerResponse,
    FeedbackResponse,
    RecommendationResponse,
    AnalyzeAnswerRequest,
    AnalyzeAnswerResponse,
    DatasetImportResponse
)
from app.services.ai_inference import ai_service
from app.services.feedback_engine import feedback_engine
from app.services.dataset_service import dataset_service
from app.services.concept_dependency import concept_dependency_service, OOP_CONCEPT_DAG
from app.services.lecture_catalog import IT2030_LECTURE_FILES, get_recommendation_for_concept

router = APIRouter(prefix="/api", tags=["RubriMark Feedback API"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Backend health check returning database status and AI model state."""
    db_status = "connected"
    try:
        db.query(Student).first()
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="RubriMark AI - Personalized Feedback Component",
        version="1.0.0",
        database=db_status,
        model_loaded=ai_service.is_loaded,
        model_status=ai_service.status_message
    )


@router.get("/model-status")
def get_model_status():
    """Returns detailed status and expected artifacts for the trained AI model."""
    return {
        "model_loaded": ai_service.is_loaded,
        "model_path": ai_service.model_path,
        "file_exists": os.path.exists(ai_service.model_path),
        "status_message": ai_service.status_message,
        "model_metadata": ai_service.model_metadata,
        "instructions": (
            "Model is loaded from 'backend/ml_models/rubrimark_oop_model.joblib'. "
            "Runs 15 binary LogisticRegression classifiers with SentenceTransformer ('all-MiniLM-L6-v2') embeddings."
        )
    }


@router.get("/students", response_model=List[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    """Retrieve all students with submission counts."""
    students = db.query(Student).all()
    results = []
    for s in students:
        results.append(
            StudentResponse(
                id=s.id,
                student_id=s.student_id,
                student_name=s.student_name,
                email=s.email,
                answers_count=len(s.answers)
            )
        )
    return results


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Retrieve single student information."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        student_name=student.student_name,
        email=student.email,
        answers_count=len(student.answers)
    )


@router.get("/questions", response_model=List[QuestionResponse])
def get_questions(db: Session = Depends(get_db)):
    """Retrieve all assessment questions."""
    return db.query(Question).all()


@router.get("/students/{student_id}/answers", response_model=List[StudentAnswerResponse])
def get_student_answers(student_id: str, db: Session = Depends(get_db)):
    """Retrieve all submitted answers for a given student with questions, feedback, and verified lecture recommendations."""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")

    EXCLUDED_META = {"none clearly identified", "requires human review"}
    from app.services.feedback_engine import QUESTION_EXPECTED_CONCEPTS

    answers = db.query(StudentAnswer).filter(StudentAnswer.student_id == student_id).order_by(StudentAnswer.question_id).all()
    response_list = []

    for ans in answers:
        fb_resp = None
        expected = QUESTION_EXPECTED_CONCEPTS.get(ans.question_id, [])
        if ans.feedback:
            raw_missing_items = [
                c.strip() for c in (ans.feedback.missing_concepts or "").replace(";", ",").split(",")
                if c.strip() and c.strip().lower() not in EXCLUDED_META
            ]
            # Separate question-relevant missing concepts from any cross-question anomalies
            missing_list = [c for c in raw_missing_items if c in expected] if expected else raw_missing_items
            unrelated_list = [c for c in raw_missing_items if c not in expected] if expected else []

            correct_list = [
                c.strip() for c in (ans.feedback.correctly_identified_concepts or "").replace(";", ",").split(",")
                if c.strip() and c.strip().lower() not in EXCLUDED_META
            ]
            expected_undetected = [c for c in expected if c not in correct_list]
            requires_human_review = (
                "requires human review" in (ans.feedback.missing_concepts or "").lower()
                or "requires instructor" in (ans.feedback.weaknesses or "").lower()
            )

            recs_list = []
            for r in ans.feedback.recommendations:
                fname = r.resource_url.split("#")[0].split("/")[-1] if "/" in r.resource_url else ""
                recs_list.append(
                    RecommendationResponse(
                        id=r.id,
                        feedback_id=r.feedback_id,
                        concept_name=r.concept_name,
                        resource_title=r.resource_title,
                        resource_type=r.resource_type or "SLIIT IT2030 Lecture PDF",
                        resource_url=r.resource_url,
                        priority_level=r.priority_level or "High",
                        lecture_number=r.lecture_number,
                        verified_page=r.verified_page,
                        reason=r.reason,
                        practice_activity=r.practice_activity,
                        download_url=r.download_url or f"/api/lectures/{fname}?download=true",
                        frontend_view_url=f"/lectures/{fname}#page={r.verified_page}" if r.verified_page else r.resource_url
                    )
                )

            fb_resp = FeedbackResponse(
                id=ans.feedback.id,
                student_answer_id=ans.feedback.student_answer_id,
                strengths=ans.feedback.strengths,
                weaknesses=ans.feedback.weaknesses,
                missing_concepts=missing_list,
                correctly_identified_concepts=correct_list,
                expected_concepts=expected,
                expected_undetected_concepts=expected_undetected,
                requires_human_review=requires_human_review,
                unrelated_cross_question_concepts=unrelated_list,
                mark_deduction_reason=ans.feedback.mark_deduction_reason,
                improvement_suggestions=ans.feedback.improvement_suggestions,
                personalized_feedback=ans.feedback.personalized_feedback,
                created_at=ans.feedback.created_at,
                recommendations=recs_list
            )

        q_resp = None
        if ans.question:
            q_resp = QuestionResponse(
                id=ans.question.id,
                question_id=ans.question.question_id,
                question_text=ans.question.question_text,
                subject=ans.question.subject,
                total_marks=ans.question.total_marks
            )

        response_list.append(
            StudentAnswerResponse(
                id=ans.id,
                student_id=ans.student_id,
                question_id=ans.question_id,
                student_answer=ans.student_answer,
                obtained_marks=ans.obtained_marks,
                submission_date=ans.submission_date,
                question=q_resp,
                feedback=fb_resp
            )
        )

    return response_list


@router.post("/analyze-answer", response_model=AnalyzeAnswerResponse)
def analyze_answer(payload: AnalyzeAnswerRequest, db: Session = Depends(get_db)):
    """
    Analyzes a student answer:
    1. Runs AI model inference using SentenceTransformer + rubrimark_oop_model.joblib.
    2. Identifies question-specific missing concepts, distinguishing from cross-question anomalies.
    3. Synthesizes transparent strengths, weaknesses, rubric marks justification, and suggestions.
    4. Matches verified SLIIT IT2030 lecture recommendations (exact page numbers, reason, practice).
    5. Optionally saves the evaluation into SQLite database.
    """
    question = db.query(Question).filter(Question.question_id == payload.question_id).first()
    question_text = question.question_text if question else f"Question {payload.question_id}"
    total_marks = question.total_marks if question else 10.0

    student = db.query(Student).filter(Student.student_id == payload.student_id).first()
    if not student and payload.save_to_db:
        student = Student(
            student_id=payload.student_id,
            student_name=f"Student {payload.student_id}",
            email=f"{payload.student_id.lower()}@rubrimark.edu"
        )
        db.add(student)
        db.flush()

    if not question and payload.save_to_db:
        question = Question(
            question_id=payload.question_id,
            question_text=question_text,
            subject="Object-Oriented Programming",
            total_marks=total_marks
        )
        db.add(question)
        db.flush()

    # Step 1: Run actual AI model inference with question ID and student ID (Requirement 2 & 3)
    ai_status = "model_inference" if ai_service.is_loaded else "model_unavailable"
    missing_concepts: List[str] = []
    ai_details: dict = {}

    if ai_service.is_loaded:
        ai_details = ai_service.predict_detailed(
            student_answer=payload.student_answer,
            question_text=question_text,
            question_id=payload.question_id,
            student_id=payload.student_id
        )
        if ai_details["success"]:
            # Substantive gaps strictly exclude metadata labels and cross-question anomalies
            missing_concepts = ai_details.get("substantive_missing_concepts", [])
            if ai_details.get("requires_human_review") or ai_details.get("is_uncertain"):
                ai_status = "model_inference_review_recommended"
            elif ai_details.get("none_identified"):
                ai_status = "model_inference_low_confidence"
        else:
            ai_status = f"model_error: {ai_details.get('message', 'unknown error')}"

    # Step 1.5: Retrieve existing assessment marks automatically from database if available (Requirement 10)
    effective_marks = payload.obtained_marks
    existing_ans_record = db.query(StudentAnswer).filter(
        StudentAnswer.student_id == payload.student_id,
        StudentAnswer.question_id == payload.question_id
    ).first()
    if effective_marks is None and existing_ans_record and existing_ans_record.obtained_marks is not None:
        effective_marks = existing_ans_record.obtained_marks

    # Step 2: Generate personalized feedback and lecture recommendations (Requirement 8 & 9)
    eval_result = feedback_engine.generate_feedback_and_recommendations(
        student_answer=payload.student_answer,
        question_text=question_text,
        obtained_marks=effective_marks,
        total_marks=total_marks,
        missing_concepts=missing_concepts,
        ai_available=ai_service.is_loaded,
        question_id=payload.question_id,
        ai_details=ai_details
    )

    final_missing = eval_result.get("substantive_missing_concepts", missing_concepts)

    # Step 3: Run Concept Dependency Analysis for root knowledge gaps (Requirement 6)
    dep_analysis = concept_dependency_service.analyze_student_profile(final_missing)
    root_gaps = [r["concept"] for r in dep_analysis.get("root_causes", [])]

    saved_id = None
    if payload.save_to_db:
        if existing_ans_record:
            existing_ans_record.student_answer = payload.student_answer
            if effective_marks is not None:
                existing_ans_record.obtained_marks = effective_marks
            ans_record = existing_ans_record
        else:
            ans_record = StudentAnswer(
                student_id=payload.student_id,
                question_id=payload.question_id,
                student_answer=payload.student_answer,
                obtained_marks=effective_marks
            )
            db.add(ans_record)
            db.flush()

        saved_id = ans_record.id

        if ans_record.feedback:
            db.delete(ans_record.feedback)
            db.flush()

        fb_record = Feedback(
            student_answer_id=ans_record.id,
            strengths=eval_result["strengths"],
            weaknesses=eval_result["weaknesses"],
            missing_concepts="; ".join(final_missing),
            correctly_identified_concepts="; ".join(eval_result.get("correctly_identified_concepts", [])),
            mark_deduction_reason=eval_result.get("mark_deduction_reason"),
            improvement_suggestions=eval_result.get("improvement_suggestions"),
            personalized_feedback=eval_result["personalized_feedback"]
        )
        db.add(fb_record)
        db.flush()

        for rec in eval_result["recommendations"]:
            db.add(
                LearningRecommendation(
                    feedback_id=fb_record.id,
                    concept_name=rec.concept_name,
                    resource_title=rec.resource_title,
                    resource_type=rec.resource_type,
                    resource_url=rec.resource_url,
                    priority_level=rec.priority_level,
                    lecture_number=rec.lecture_number,
                    verified_page=rec.verified_page,
                    reason=rec.reason,
                    practice_activity=rec.practice_activity,
                    download_url=rec.download_url
                )
            )

        db.commit()

    return AnalyzeAnswerResponse(
        student_id=payload.student_id,
        question_id=payload.question_id,
        student_answer=payload.student_answer,
        obtained_marks=effective_marks,
        total_marks=total_marks,
        ai_status=ai_status,
        missing_concepts=final_missing,
        correctly_identified_concepts=eval_result.get("correctly_identified_concepts", []),
        expected_concepts=ai_details.get("expected_concepts", []),
        expected_undetected_concepts=eval_result.get("expected_undetected_concepts", []),
        requires_human_review=ai_details.get("requires_human_review", False) or eval_result.get("requires_human_review", False),
        uncertainty_info=ai_details.get("uncertainty_info"),
        unrelated_cross_question_concepts=ai_details.get("unrelated_cross_question_concepts", []),
        cross_question_anomalies_filtered=ai_details.get("cross_question_anomalies_filtered", []),
        mark_deduction_reason=eval_result.get("mark_deduction_reason"),
        improvement_suggestions=eval_result.get("improvement_suggestions"),
        strengths=eval_result["strengths"],
        weaknesses=eval_result["weaknesses"],
        personalized_feedback=eval_result["personalized_feedback"],
        recommendations=eval_result["recommendations"],
        root_knowledge_gaps=root_gaps,
        saved_answer_id=saved_id
    )


@router.get("/students/{student_id}/feedback")
def get_student_feedback(student_id: str, db: Session = Depends(get_db)):
    """Retrieve all personalized feedback entries for a student."""
    EXCLUDED_META = {"none clearly identified", "requires human review"}
    answers = db.query(StudentAnswer).filter(StudentAnswer.student_id == student_id).order_by(StudentAnswer.question_id).all()
    if not answers:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
        return []

    from app.services.feedback_engine import QUESTION_EXPECTED_CONCEPTS

    results = []
    for ans in answers:
        if ans.feedback:
            expected = QUESTION_EXPECTED_CONCEPTS.get(ans.question_id, [])
            raw_missing = ans.feedback.missing_concepts or ""
            raw_missing_items = [
                c.strip() for c in raw_missing.replace(";", ",").split(",")
                if c.strip() and c.strip().lower() not in EXCLUDED_META
            ]
            # Isolate question-relevant from cross-question concepts
            missing_list = [c for c in raw_missing_items if c in expected] if expected else raw_missing_items
            unrelated_list = [c for c in raw_missing_items if c not in expected] if expected else []

            raw_correct = ans.feedback.correctly_identified_concepts or ""
            correct_list = [
                c.strip() for c in raw_correct.replace(";", ",").split(",")
                if c.strip() and c.strip().lower() not in EXCLUDED_META
            ]
            expected_undetected = [c for c in expected if c not in correct_list]
            requires_human_review = (
                "requires human review" in raw_missing.lower()
                or "requires instructor" in (ans.feedback.weaknesses or "").lower()
            )
            recs_list = [
                {
                    "id": r.id,
                    "concept_name": r.concept_name,
                    "resource_title": r.resource_title,
                    "resource_type": r.resource_type,
                    "resource_url": r.resource_url,
                    "priority_level": r.priority_level,
                    "lecture_number": r.lecture_number,
                    "verified_page": r.verified_page,
                    "reason": r.reason,
                    "practice_activity": r.practice_activity,
                    "download_url": r.download_url,
                    "frontend_view_url": f"/lectures/{r.resource_url.split('#')[0].split('/')[-1]}#page={r.verified_page}" if r.verified_page else r.resource_url
                }
                for r in ans.feedback.recommendations
            ]
            results.append({
                "feedback_id": ans.feedback.id,
                "answer_id": ans.id,
                "question_id": ans.question_id,
                "question_text": ans.question.question_text if ans.question else None,
                "student_answer": ans.student_answer,
                "obtained_marks": ans.obtained_marks,
                "total_marks": ans.question.total_marks if ans.question else None,
                "strengths": ans.feedback.strengths,
                "weaknesses": ans.feedback.weaknesses,
                "missing_concepts": missing_list,
                "correctly_identified_concepts": correct_list,
                "expected_concepts": expected,
                "expected_undetected_concepts": expected_undetected,
                "unrelated_cross_question_concepts": unrelated_list,
                "requires_human_review": requires_human_review,
                "mark_deduction_reason": ans.feedback.mark_deduction_reason,
                "improvement_suggestions": ans.feedback.improvement_suggestions,
                "personalized_feedback": ans.feedback.personalized_feedback,
                "created_at": ans.feedback.created_at,
                "recommendations": recs_list
            })
    return results


@router.get("/students/{student_id}/recommendations", response_model=List[RecommendationResponse])
def get_student_recommendations(student_id: str, db: Session = Depends(get_db)):
    """Retrieve learning recommendations aggregated across all answers of a student."""
    answers = db.query(StudentAnswer).filter(StudentAnswer.student_id == student_id).order_by(StudentAnswer.question_id).all()
    if not answers:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
        return []

    all_recommendations = []
    seen_concepts = set()

    for ans in answers:
        if ans.feedback:
            for r in ans.feedback.recommendations:
                if r.concept_name not in seen_concepts:
                    seen_concepts.add(r.concept_name)
                    fname = r.resource_url.split("#")[0].split("/")[-1] if "/" in r.resource_url else ""
                    all_recommendations.append(
                        RecommendationResponse(
                            id=r.id,
                            feedback_id=r.feedback_id,
                            concept_name=r.concept_name,
                            resource_title=r.resource_title,
                            resource_type=r.resource_type or "SLIIT IT2030 Lecture PDF",
                            resource_url=r.resource_url,
                            priority_level=r.priority_level or "High",
                            lecture_number=r.lecture_number,
                            verified_page=r.verified_page,
                            reason=r.reason,
                            practice_activity=r.practice_activity,
                            download_url=r.download_url or f"/api/lectures/{fname}?download=true",
                            frontend_view_url=f"/lectures/{fname}#page={r.verified_page}" if r.verified_page else r.resource_url
                        )
                    )
    return all_recommendations


@router.post("/import-dataset", response_model=DatasetImportResponse)
async def import_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and validate a student answers CSV dataset."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are accepted.")

    content = await file.read()
    res = dataset_service.validate_and_import_csv(content, db, filename=file.filename)
    return DatasetImportResponse(**res)


@router.post("/seed-demo-data")
def seed_demo_data(db: Session = Depends(get_db)):
    """Seed initial academic benchmark dataset."""
    success = dataset_service.seed_initial_academic_dataset(db)
    return {
        "status": "success",
        "seeded": success,
        "message": "Academic benchmark dataset ready." if success else "Database already contains student records."
    }


# ============================================================================
# IT23436244 Research Component: Concept Dependency Analysis Endpoints
# ============================================================================

@router.get("/concept-dependencies")
def get_curriculum_concept_dependencies():
    """
    Returns the complete OOP curriculum Concept Dependency Directed Acyclic Graph (DAG),
    including modules, difficulty levels, descriptions, and prerequisite links.
    (IT23436244 Research Component)
    """
    nodes = []
    edges = []
    for concept, meta in OOP_CONCEPT_DAG.items():
        nodes.append({
            "id": meta["id"],
            "label": concept,
            "module": meta["module"],
            "question_id": meta["question_id"],
            "difficulty": meta["difficulty"],
            "description": meta["description"]
        })
        for prereq in meta["prerequisites"]:
            if prereq in OOP_CONCEPT_DAG:
                edges.append({
                    "from": OOP_CONCEPT_DAG[prereq]["id"],
                    "to": meta["id"],
                    "prereq_name": prereq,
                    "target_name": concept
                })
    return {
        "research_component": {
            "title": "Concept Dependency Analysis & Prerequisite DAG Framework",
            "framework": "RubriMark AI"
        },
        "total_concepts": len(nodes),
        "nodes": nodes,
        "edges": edges
    }


@router.get("/students/{student_id}/concept-dependencies")
def get_student_concept_dependencies(student_id: str, db: Session = Depends(get_db)):
    """
    Executes Concept Dependency Analysis for a specific student:
    - Collects detected knowledge gaps across all their submissions.
    - Diagnoses root causes vs isolated gaps.
    - Identifies downstream at-risk concepts.
    - Produces a topologically sorted learning remediation path.
    """
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")

    EXCLUDED_META = {"none clearly identified", "requires human review"}
    answers = db.query(StudentAnswer).filter(StudentAnswer.student_id == student_id).order_by(StudentAnswer.question_id).all()
    all_missing_concepts: List[str] = []

    for ans in answers:
        if ans.feedback and ans.feedback.missing_concepts:
            raw = ans.feedback.missing_concepts
            concepts = [
                c.strip() for c in raw.replace(";", ",").split(",")
                if c.strip() and c.strip().lower() not in EXCLUDED_META
            ]
            all_missing_concepts.extend(concepts)

    analysis = concept_dependency_service.analyze_student_profile(all_missing_concepts)
    analysis["student"] = {
        "student_id": student.student_id,
        "student_name": student.student_name,
        "email": student.email,
        "answers_submitted": len(answers)
    }
    return analysis


@router.post("/predict-missing-concepts")
def direct_predict_missing_concepts(payload: AnalyzeAnswerRequest):
    """
    Direct model inference endpoint to evaluate arbitrary student text using the trained
    rubrimark_oop_model.joblib, returning detailed probabilities across all 15 classes.
    """
    if not ai_service.is_loaded:
        raise HTTPException(status_code=503, detail="AI Model is not currently loaded.")

    res = ai_service.predict_detailed(payload.student_answer)
    return res


# ============================================================================
# Verified SLIIT IT2030 Lecture Materials Endpoints
# ============================================================================

@router.get("/lectures")
def get_lectures_list():
    """Returns the list of all 10 verified SLIIT IT2030 lecture PDF documents."""
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(here))
    materials_dir = os.path.join(backend_dir, "lecture_materials")

    lectures = []
    for num, meta in IT2030_LECTURE_FILES.items():
        fname = meta["filename"]
        fpath = os.path.join(materials_dir, fname)
        size_bytes = os.path.getsize(fpath) if os.path.exists(fpath) else 0
        lectures.append({
            "lecture_number": num,
            "title": meta["title"],
            "filename": fname,
            "total_pages": meta["total_pages"],
            "size_bytes": size_bytes,
            "view_url": f"/api/lectures/{fname}",
            "download_url": f"/api/lectures/{fname}?download=true",
            "frontend_view_url": f"/lectures/{fname}"
        })
    return lectures


@router.get("/lectures/{filename}")
@router.head("/lectures/{filename}")
def get_lecture_pdf(filename: str, download: bool = False):
    """
    Serves a verified SLIIT IT2030 lecture PDF with headers for inline viewing or attachment download.
    Path traversal is prevented by resolving and checking the canonical path.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(here))
    materials_dir = os.path.realpath(os.path.join(backend_dir, "lecture_materials"))

    import urllib.parse

    # Sanitise and unquote filename – strip any path components (prevent directory traversal)
    safe_filename = urllib.parse.unquote(os.path.basename(filename))
    file_path = os.path.realpath(os.path.join(materials_dir, safe_filename))

    # Ensure the resolved path is still inside lecture_materials
    if not file_path.startswith(materials_dir):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    if not os.path.exists(file_path):
        # Fallback case-insensitive lookup across materials_dir
        candidate = None
        for existing in os.listdir(materials_dir):
            if existing.lower() == safe_filename.lower():
                candidate = existing
                break
        if candidate:
            file_path = os.path.realpath(os.path.join(materials_dir, candidate))
            safe_filename = candidate
        else:
            raise HTTPException(status_code=404, detail=f"Lecture PDF '{safe_filename}' not found.")

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Accept-Ranges": "bytes",
    }
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
    else:
        headers["Content-Disposition"] = f'inline; filename="{safe_filename}"'

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers=headers
    )


# ============================================================================
# IT23436244 Research Component: Student Dashboard Statistics Endpoint
# ============================================================================

@router.get("/students/{student_id}/dashboard")
@router.get("/students/{student_id}/dashboard-stats")
def get_student_dashboard_stats(student_id: str, db: Session = Depends(get_db)):
    """
    Returns an authentic, explainable set of real statistics for the student dashboard:
    - Questions Answered, Feedback counts, Concept counts, Root knowledge gaps, Recommendation counts
    - Distinguishes correctly identified concepts vs expected but undetected concepts vs confirmed gaps
    - Knowledge gap distribution grouped by standard OOP topics
    - Recommendation priority distribution (High, Medium, Low)
    - Per-question concept coverage data for Q1-Q5
    (IT23436244 Research Component)
    """
    from app.services.feedback_engine import QUESTION_EXPECTED_CONCEPTS

    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")

    answers = db.query(StudentAnswer).filter(StudentAnswer.student_id == student_id).order_by(StudentAnswer.question_id).all()

    total_answers = len(answers)
    total_feedback = 0
    total_recommendations = 0
    all_missing = []
    all_identified = []
    expected_concepts_for_student = []

    # Excluded metadata labels as per research specification
    EXCLUDED_META = {"None clearly identified", "requires human review"}

    # Per-question concept coverage for Chart 4
    question_coverage = []
    for qid in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        expected = QUESTION_EXPECTED_CONCEPTS.get(qid, [])
        ans = next((a for a in answers if a.question_id == qid), None)
        if ans:
            for exp_c in expected:
                expected_concepts_for_student.append(exp_c)

            if ans.feedback:
                raw_missing = ans.feedback.missing_concepts or ""
                missing = [c.strip() for c in raw_missing.replace(";", ",").split(",")
                           if c.strip() and c.strip() not in EXCLUDED_META]
                raw_correct = ans.feedback.correctly_identified_concepts or ""
                identified = [c.strip() for c in raw_correct.replace(";", ",").split(",")
                              if c.strip() and c.strip() not in EXCLUDED_META]
            else:
                missing = []
                identified = []
        else:
            missing = []
            identified = []

        question_coverage.append({
            "question": qid,
            "expected": len(expected),
            "identified": len(identified),
            "missing": len(missing),
        })

    # Aggregate across all answers for this student
    for ans in answers:
        if ans.feedback:
            total_feedback += 1
            raw_missing = ans.feedback.missing_concepts or ""
            gaps = [c.strip() for c in raw_missing.replace(";", ",").split(",")
                    if c.strip() and c.strip() not in EXCLUDED_META]
            all_missing.extend(gaps)

            raw_correct = ans.feedback.correctly_identified_concepts or ""
            identified = [c.strip() for c in raw_correct.replace(";", ",").split(",")
                          if c.strip() and c.strip() not in EXCLUDED_META]
            all_identified.extend(identified)

            total_recommendations += len(ans.feedback.recommendations)

    # Unique concept sets
    unique_missing = list(dict.fromkeys(all_missing))
    unique_identified = list(dict.fromkeys(all_identified))

    # Expected curriculum concepts for the student's answered questions
    # Undetected concepts = expected concepts that the student did not demonstrate
    unique_expected = list(dict.fromkeys(expected_concepts_for_student))
    expected_undetected = [c for c in unique_expected if c not in unique_identified]

    # Run Concept Dependency Analysis for Root Knowledge Gaps (IT23436244)
    dep_analysis = concept_dependency_service.analyze_student_profile(all_missing)
    root_causes = dep_analysis.get("root_causes", [])
    root_gaps = [r["concept"] for r in root_causes]
    root_gap_count = len(root_causes)

    # Knowledge gap distribution grouped into relevant OOP topics (Chart 2)
    topic_map = {
        "Classes and Objects": [
            "Class as blueprint/template",
            "Object as class instance",
            "Concrete class-object example"
        ],
        "Inheritance": [
            "Inheritance of accessible fields",
            "Inheritance of accessible methods"
        ],
        "Method Overriding": [
            "Child provides overriding implementation",
            "Child implementation executes on child object"
        ],
        "Static and Instance Variables": [
            "Static belongs to class",
            "instance variable belongs to object",
            "No direct instance-variable access from static method",
            "Instance reference required for access"
        ],
        "Exception Handling": [
            "Handles runtime exceptions/errors",
            "Prevents abrupt termination or supports graceful recovery"
        ],
    }
    gap_distribution = []
    for topic, concepts in topic_map.items():
        count = sum(1 for c in all_missing if c in concepts)
        gap_distribution.append({"topic": topic, "missing_count": count})

    # Recommendation priority distribution (Chart 3)
    priority_counts = {"High": 0, "Medium": 0, "Low": 0}
    for ans in answers:
        if ans.feedback:
            for rec in ans.feedback.recommendations:
                pl = (rec.priority_level or "Medium").strip().capitalize()
                if pl in priority_counts:
                    priority_counts[pl] += 1
                else:
                    priority_counts["Medium"] += 1

    priority_distribution = [
        {"priority": "High", "count": priority_counts["High"]},
        {"priority": "Medium", "count": priority_counts["Medium"]},
        {"priority": "Low", "count": priority_counts["Low"]},
    ]

    return {
        "student_id": student.student_id,
        "student_name": student.student_name,
        "email": student.email,
        "summary": {
            "questions_answered": total_answers,
            "total_answers": total_answers,
            "concepts_identified": len(unique_identified),
            "total_identified_concepts": len(unique_identified),
            "missing_concepts": len(unique_missing),
            "total_missing_concepts": len(unique_missing),
            "root_knowledge_gaps": root_gap_count,
            "root_gaps_count": root_gap_count,
            "personalized_feedback_records": total_feedback,
            "total_feedback_records": total_feedback,
            "learning_recommendations": total_recommendations,
            "total_recommendations": total_recommendations,
            "expected_undetected_count": len(expected_undetected),
            "ai_analysis_status": "completed" if total_feedback > 0 else "pending",
        },
        "identified_concepts": unique_identified,
        "missing_concepts": unique_missing,
        "expected_undetected_concepts": expected_undetected,
        "root_knowledge_gaps": root_gaps,
        "question_coverage": question_coverage,
        "gap_distribution": gap_distribution,
        "priority_distribution": priority_distribution,
    }


