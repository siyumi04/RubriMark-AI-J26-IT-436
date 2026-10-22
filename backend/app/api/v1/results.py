from collections import defaultdict
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.submission import StudentSubmission, CriterionScore
from app.schemas.submission import AssessmentResultsSummary

router = APIRouter(prefix="/results", tags=["8. Assessment Results & Analytics"])


@router.get("/assessment/{assessment_id}", response_model=AssessmentResultsSummary)
def get_assessment_results(assessment_id: int, db: Session = Depends(get_db)):
    """
    Feature 8: Assessment Results.
    Computes cohort statistics, score distribution, and criterion-specific performance metrics.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    submissions = db.query(StudentSubmission).filter(StudentSubmission.assessment_id == assessment_id).all()
    count = len(submissions)

    if count == 0:
        return {
            "assessment_id": assessment.id,
            "assessment_title": assessment.title,
            "total_submissions": 0,
            "average_score": 0.0,
            "highest_score": 0.0,
            "lowest_score": 0.0,
            "pass_rate": 0.0,
            "criterion_performance": []
        }

    scores = [s.total_score for s in submissions]
    avg_score = round(sum(scores) / count, 2)
    max_score = round(max(scores), 2)
    min_score = round(min(scores), 2)
    passed = sum(1 for s in submissions if s.percentage >= 50.0)
    pass_rate = round((passed / count) * 100.0, 1)

    # Per criterion aggregation
    criterion_data = defaultdict(lambda: {"total_score": 0.0, "max_score": 0.0, "count": 0, "name": ""})
    for sub in submissions:
        for cs in sub.criterion_scores:
            entry = criterion_data[cs.criterion_name]
            entry["total_score"] += cs.score_awarded
            entry["max_score"] = cs.max_score
            entry["count"] += 1
            entry["name"] = cs.criterion_name

    criterion_performance = []
    for name, data in criterion_data.items():
        avg_c = round(data["total_score"] / data["count"], 2) if data["count"] > 0 else 0.0
        perf_pct = round((avg_c / data["max_score"]) * 100.0, 1) if data["max_score"] > 0 else 0.0
        criterion_performance.append({
            "criterion_name": name,
            "average_score": avg_c,
            "max_score": data["max_score"],
            "performance_percentage": perf_pct,
            "status": "strong" if perf_pct >= 75 else ("moderate" if perf_pct >= 50 else "needs_attention")
        })

    return {
        "assessment_id": assessment.id,
        "assessment_title": assessment.title,
        "total_submissions": count,
        "average_score": avg_score,
        "highest_score": max_score,
        "lowest_score": min_score,
        "pass_rate": pass_rate,
        "criterion_performance": criterion_performance
    }
