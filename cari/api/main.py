"""FastAPI service for Component 2.  Run: uvicorn cari.api.main:app --reload
Env: CARI_ENGINE_PATH (default models/engine.joblib), DATABASE_URL."""
from __future__ import annotations
import os
import csv
import io
import re
import smtplib
from email.message import EmailMessage
from typing import Literal, Optional
import joblib
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ..contract import AssessmentCase, ReliabilityResult
from ..db import Assessment, EmailDelivery, LecturerDecision, make_session_factory

app = FastAPI(title="RubriMark AI - Component 2: Reliability Decision Engine", version="1.0")
_state: dict = {}
_frontend_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")


def get_engine():
    if "engine" not in _state:
        path = os.getenv("CARI_ENGINE_PATH", "models/engine.joblib")
        if not os.path.exists(path):
            raise HTTPException(503, f"Engine artifact not found at {path}; run scripts/run_experiment.py first")
        _state["engine"] = joblib.load(path)
    return _state["engine"]


def get_db():
    if "sf" not in _state:
        _state["sf"] = make_session_factory()
    db = _state["sf"]()
    try:
        yield db
    finally:
        db.close()


class DecisionIn(BaseModel):
    assessment_id: str
    action: Literal["approve", "override"]
    final_score: Optional[float] = None
    comment: Optional[str] = None


class ScoreEditIn(BaseModel):
    final_score: float
    comment: Optional[str] = None


QUESTION_IDS = ("oop_q1_class_object", "oop_q2_inheritance", "oop_q3_overriding",
                "oop_q4_static_instance", "oop_q5_exceptions")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(os.path.join(_frontend_dir, "index.html"))


@app.get("/styles.css", include_in_schema=False)
def frontend_styles():
    return FileResponse(os.path.join(_frontend_dir, "styles.css"))


@app.get("/app.js", include_in_schema=False)
def frontend_script():
    return FileResponse(os.path.join(_frontend_dir, "app.js"))


@app.get("/health")
def health():
    return {"status": "ok", "engine_loaded": "engine" in _state}


@app.post("/assess", response_model=ReliabilityResult)
def assess(case: AssessmentCase, db=Depends(get_db), engine=Depends(get_engine)):
    res = engine.assess(case)
    status = "released" if res.decision == "AUTO_RELEASE" else "pending"
    row = Assessment(assessment_id=case.assessment_id, question_id=case.question_id, payload=case.model_dump(mode="json"),
                     cari=res.cari, decision=res.decision, gates=res.gates_fired, indicators=res.indicators,
                     reason=res.reason, config_id=res.config_id, tau=res.tau, status=status)
    db.merge(row)
    db.commit()
    return res


@app.get("/queue")
def queue(limit: int = 1000, db=Depends(get_db)):
    """Cases awaiting lecturer validation, least reliable first."""
    rows = (db.query(Assessment).filter(Assessment.decision == "LECTURER_VALIDATION", Assessment.status == "pending")
            .order_by(Assessment.cari.is_(None).desc(), Assessment.cari.asc()).limit(limit).all())
    return [{"assessment_id": r.assessment_id, "question_id": r.question_id, "cari": r.cari, "gates": r.gates,
             "reason": r.reason, "student_response": r.payload["student_response"], "ai_score": r.payload["c3"]["ai_score"] if r.payload.get("c3") else None}
            for r in rows]


@app.get("/dashboard")
def dashboard(db=Depends(get_db)):
    """Summary cards for the lecturer dashboard."""
    total = db.query(Assessment).count()
    released = db.query(Assessment).filter(Assessment.status == "released").count()
    pending = db.query(Assessment).filter(
        Assessment.decision == "LECTURER_VALIDATION", Assessment.status == "pending"
    ).count()
    reviewed = db.query(Assessment).filter(Assessment.status == "reviewed").count()
    return {
        "total": total,
        "released": released,
        "pending_validation": pending,
        "queue_limit": 1000,
        "reviewed": reviewed,
        "release_rate": round(released / total * 100, 1) if total else 0,
    }


@app.get("/results")
def results(limit: int = 100, status: Optional[Literal["released", "reviewed"]] = None, db=Depends(get_db)):
    """Results released automatically or after lecturer review."""
    query = db.query(Assessment)
    if status:
        query = query.filter(Assessment.status == status)
    rows = query.order_by(Assessment.created_at.desc()).limit(limit).all()
    return [_result_payload(r, db) for r in rows]


@app.get("/results/export.csv")
def export_results(db=Depends(get_db)):
    """Download complete student totals and Component 4 feedback only."""
    rows = db.query(Assessment).order_by(Assessment.assessment_id).all()
    grouped: dict[str, list[dict]] = {}
    feedback_by_student: dict[str, list[str]] = {}
    for row in rows:
        result = _result_payload(row, db)
        student_id = _student_id(row.assessment_id)
        grouped.setdefault(student_id, []).append(result)
        c4 = row.payload.get("c4") or {}
        feedback_by_student.setdefault(student_id, []).extend(c4.get("direct_gaps") or [])
        feedback_by_student[student_id].extend(c4.get("root_causes") or [])
    question_ids = sorted({result["question_id"] for result in sum(grouped.values(), [])})
    # Keep the five OOP columns stable even when some questions are still pending.
    for question_id in QUESTION_IDS:
        if question_id not in question_ids:
            question_ids.append(question_id)
    headers = ["student_id"] + [f"{qid}_score" for qid in question_ids] + [
        "total_score", "max_total_score", "feedback"
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for student_id, student_results in grouped.items():
        values = {result["question_id"]: result for result in student_results}
        if not all(q in values and values[q]["status"] in ("released", "reviewed") for q in QUESTION_IDS):
            continue
        record = {"student_id": student_id}
        total = 0.0
        max_total = 0.0
        for question_id in question_ids:
            result = values.get(question_id)
            record[f"{question_id}_score"] = "" if result is None else result["final_score"]
            if result is not None:
                total += result["final_score"] or 0
                max_total += result["max_score"] or 0
        record["total_score"] = total
        record["max_total_score"] = max_total
        feedback_items = list(dict.fromkeys(feedback_by_student.get(student_id, [])))
        record["feedback"] = (
            "Review " + ", ".join(feedback_items) + "."
            if feedback_items else "Continue practising the assessed concepts."
        )
        writer.writerow(record)
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="student_marks.csv"'})


@app.get("/student-results")
def student_results(db=Depends(get_db)):
    """Final-release view: one row per student across all five questions."""
    rows = db.query(Assessment).order_by(Assessment.assessment_id).all()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(_student_id(row.assessment_id), []).append(_result_payload(row, db))
    output = []
    for student_id, items in grouped.items():
        by_question = {item["question_id"]: item for item in items}
        complete = all(q in by_question and by_question[q]["status"] in ("released", "reviewed") for q in QUESTION_IDS)
        output.append({
            "student_id": student_id,
            "student_email": next((i["student_email"] for i in items if i["student_email"]), f"{student_id}@example.edu"),
            "question_scores": {q: (by_question[q]["final_score"] if q in by_question and by_question[q]["status"] in ("released", "reviewed") else None) for q in QUESTION_IDS},
            "total_score": sum((by_question[q]["final_score"] or 0) for q in QUESTION_IDS if q in by_question and by_question[q]["status"] in ("released", "reviewed")),
            "max_total_score": sum((by_question[q]["max_score"] or 0) for q in QUESTION_IDS if q in by_question and by_question[q]["status"] in ("released", "reviewed")),
            "complete": complete,
            "released_questions": sum(1 for q in QUESTION_IDS if q in by_question and by_question[q]["status"] in ("released", "reviewed")),
            "sample_data": any(i.get("sample_data") for i in items),
        })
    return output


def _student_id(assessment_id: str) -> str:
    match = re.match(r"^(.*?_\d{3})_", assessment_id)
    return match.group(1) if match else assessment_id.rsplit("_", 1)[0]


def _result_payload(row: Assessment, db) -> dict:
    payload = row.payload
    c3 = payload.get("c3") or {}
    latest_decision = (db.query(LecturerDecision)
                       .filter(LecturerDecision.assessment_id == row.assessment_id)
                       .order_by(LecturerDecision.created_at.desc(), LecturerDecision.id.desc())
                       .first())
    final_score = c3.get("ai_score")
    review_note = None
    review_action = None
    if latest_decision is not None:
        review_action = latest_decision.action
        final_score = latest_decision.final_score if latest_decision.action == "override" else final_score
        review_note = latest_decision.comment
    return {
        "assessment_id": row.assessment_id,
        "question_id": row.question_id,
        "status": row.status,
        "decision": row.decision,
        "cari": row.cari,
        "tau": row.tau,
        "threshold_note": f"Automatic release threshold (tau): {row.tau:.4f}. "
                           + ("CARI meets the threshold." if row.cari is not None and row.cari >= row.tau
                              else "CARI is below the threshold and requires validation."),
        "gates": row.gates,
        "reason": row.reason,
        "student_response": payload.get("student_response", ""),
        "student_email": payload.get("student_email"),
        "sample_data": bool(payload.get("sample_data")),
        "ai_score": c3.get("ai_score"),
        "final_score": final_score,
        "max_score": c3.get("max_score"),
        "review_action": review_action,
        "review_note": review_note,
        "criteria": c3.get("criteria", []),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@app.put("/results/{assessment_id}/score")
def edit_result_score(assessment_id: str, edit: ScoreEditIn, db=Depends(get_db)):
    row = db.get(Assessment, assessment_id)
    if row is None:
        raise HTTPException(404, "unknown assessment_id")
    c3 = row.payload.get("c3") or {}
    max_score = c3.get("max_score")
    if edit.final_score < 0 or (max_score is not None and edit.final_score > max_score):
        raise HTTPException(422, f"final_score must be between 0 and {max_score}")
    db.add(LecturerDecision(assessment_id=assessment_id, action="override",
                            final_score=edit.final_score, comment=edit.comment))
    row.status = "reviewed"
    db.commit()
    return {"assessment_id": assessment_id, "status": row.status, "final_score": edit.final_score}


@app.post("/results/{assessment_id}/email")
def email_result(assessment_id: str, db=Depends(get_db)):
    """Create a sample feedback email; production SMTP integration can replace this adapter."""
    row = db.get(Assessment, assessment_id)
    if row is None:
        raise HTTPException(404, "unknown assessment_id")
    if row.status not in ("released", "reviewed"):
        raise HTTPException(409, "result must be released before emailing")
    result = _result_payload(row, db)
    recipient = result["student_email"] or f"{_student_id(assessment_id)}@example.edu"
    gaps = (row.payload.get("c4") or {}).get("direct_gaps") or ["No additional gaps identified"]
    subject = f"Assessment result: {row.question_id}"
    body = (f"Your final score is {result['final_score']:.2f} / {result['max_score']:.2f}.\n\n"
            f"Feedback: Review the concepts related to {', '.join(gaps)}.\n"
            "This is a sample delivery from RubriMark; no external email was sent.")
    db.add(EmailDelivery(assessment_id=assessment_id, recipient=recipient, subject=subject, body=body))
    db.commit()
    return {"status": "sample_sent", "recipient": recipient, "subject": subject, "body": body}


@app.post("/students/{student_id}/email")
def email_student_result(student_id: str, db=Depends(get_db)):
    """Send the complete five-question result and Component 4 suggestions."""
    rows = [r for r in db.query(Assessment).all() if _student_id(r.assessment_id) == student_id]
    if not rows:
        raise HTTPException(404, "unknown student_id")
    results_by_q = {r.question_id: _result_payload(r, db) for r in rows}
    if not all(q in results_by_q and results_by_q[q]["status"] in ("released", "reviewed") for q in QUESTION_IDS):
        raise HTTPException(409, "all five question results must be released before emailing")
    recipient = next((r["student_email"] for r in results_by_q.values() if r["student_email"]), f"{student_id}@example.edu")
    total = sum(results_by_q[q]["final_score"] or 0 for q in QUESTION_IDS)
    maximum = sum(results_by_q[q]["max_score"] or 0 for q in QUESTION_IDS)
    suggestions = []
    for row in rows:
        suggestions.extend((row.payload.get("c4") or {}).get("direct_gaps") or [])
    unique_suggestions = list(dict.fromkeys(suggestions)) or ["Continue practising the assessed concepts."]
    subject = "Your final assessment result and feedback"
    question_scores = ", ".join(
        f"{q}: {results_by_q[q]['final_score']:.2f}" for q in QUESTION_IDS
    )
    body = (f"Your final total score is {total:.2f} / {maximum:.2f}.\n\n"
            f"Question scores: {question_scores}\n\n"
            f"Learning suggestions: Review {', '.join(unique_suggestions)}.\n")
    mode = "sample"
    if os.getenv("SMTP_HOST"):
        message = EmailMessage()
        message["From"] = os.environ["SMTP_FROM"]
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))) as smtp:
            smtp.starttls()
            smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            smtp.send_message(message)
        mode = "smtp"
    db.add(EmailDelivery(assessment_id=rows[0].assessment_id, recipient=recipient,
                         subject=subject, body=body, mode=mode))
    db.commit()
    return {"status": "sent" if mode == "smtp" else "sample_sent", "mode": mode,
            "recipient": recipient, "subject": subject, "body": body}


@app.post("/lecturer-decision")
def lecturer_decision(d: DecisionIn, db=Depends(get_db)):
    row = db.get(Assessment, d.assessment_id)
    if row is None:
        raise HTTPException(404, "unknown assessment_id")
    if d.action == "override" and d.final_score is None:
        raise HTTPException(422, "final_score is required for override")
    db.add(LecturerDecision(assessment_id=d.assessment_id, action=d.action, final_score=d.final_score, comment=d.comment))
    row.status = "released" if d.action == "approve" else "reviewed"
    db.commit()
    return {"assessment_id": d.assessment_id, "status": row.status, "action": d.action}
