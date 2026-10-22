"""
Unit and Integration Tests for Benchmark-Specific Filtering in RubriMark AI.

Validates:
1. Verification of Java OOP benchmark assessment identities before filtering by ID.
2. Dataset status endpoint (/dataset/status) with scope='benchmark' vs scope='full'.
3. Research metrics endpoint (/dataset/research-metrics) with scope='benchmark' vs scope='full'.
4. Proper provenance and respondent distinction (62 questionnaire records, 59 unique respondents, 310 answers).
5. Benchmark semantic mean verified at 59.62% (310 fixed submissions, IDs 47-51).
6. Full-scope mean dynamically verified against current live database state.
7. Keyword baseline reported as Not Evaluated (None) until explicit baseline evaluation exists.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.assessment import Assessment
from app.models.submission import StudentSubmission
from app.services.dataset_service import DatasetService

client = TestClient(app)


def test_get_verified_benchmark_assessments_identifies_all_five_questions():
    """
    Task 3: Verify benchmark assessment identities before filtering by IDs.
    Ensures assessments match known question content signatures, course code, and max marks.
    """
    db = SessionLocal()
    try:
        assessments = DatasetService.get_verified_benchmark_assessments(db)
        assert len(assessments) == 5, f"Expected 5 verified benchmark assessments, found {len(assessments)}"
        
        expected_signatures = [
            "class and an object",
            "car class extends a vehicle class",
            "child class overrides a method",
            "static method directly access",
            "exception handling important"
        ]
        
        for sig in expected_signatures:
            match = any(sig in (a.question_text or "").lower() for a in assessments)
            assert match, f"Signature '{sig}' not matched in verified benchmark questions"

        for a in assessments:
            assert a.course_code == "IT4360"
            assert a.max_marks == 10.0
    finally:
        db.close()


def test_get_csv_questionnaire_stats_provenance():
    """
    Task 6 & 7: Distinguish questionnaire response records from unique respondents.
    Ensures respondents are read directly from source CSV without DB ID truncation artifacts.
    """
    csv_stats = DatasetService.get_csv_questionnaire_stats()
    assert csv_stats["total_response_records"] == 62, "Must report 62 questionnaire form responses"
    assert csv_stats["unique_respondents"] == 59, "Must report 59 unique respondents (58 named + anonymous group)"
    assert "Source CSV" in csv_stats["provenance"]


def test_dataset_status_benchmark_scope():
    """
    Task 4: Display 5 benchmark questions, 310 scored answers, and 59 unique respondents in benchmark scope.
    """
    response = client.get("/api/v1/dataset/status?scope=benchmark")
    assert response.status_code == 200
    data = response.json()

    assert data["scope"] == "benchmark"
    assert data["assessments_count"] == 5
    assert data["submissions_count"] == 310
    assert data["scored_count"] == 310
    assert data["unique_students_count"] == 59

    stats = data["dataset_statistics"]
    assert stats["total_benchmark_questions"] == 5
    assert stats["total_student_submissions"] == 310
    assert stats["individual_answer_submissions"] == 310
    assert stats["questionnaire_response_records"] == 62
    assert stats["unique_respondents_count"] == 59
    assert stats["total_evaluated_submissions"] == 310
    assert stats["criterion_scores_count"] == 992
    assert stats["ground_truth_status"] == "Pending Lecturer"


def test_dataset_status_full_scope():
    """
    Task 5: Verify full database scope properly aggregates all assessments and scored submissions (>= 199 assessments, >= 333 submissions).
    """
    response = client.get("/api/v1/dataset/status?scope=full")
    assert response.status_code == 200
    data = response.json()

    assert data["scope"] == "full"
    assert data["assessments_count"] >= 199
    assert data["submissions_count"] >= 333
    assert data["scored_count"] >= 333

    stats = data["dataset_statistics"]
    assert stats["total_benchmark_questions"] == data["assessments_count"]
    assert stats["total_student_submissions"] == data["submissions_count"]
    assert stats["total_evaluated_submissions"] == data["scored_count"]


def test_research_metrics_benchmark_scope():
    """
    Task 4 & 8: Verify 59.62% semantic mean and Not Evaluated keyword baseline in benchmark scope.
    """
    response = client.get("/api/v1/dataset/research-metrics?scope=benchmark")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["scope"] == "benchmark"
    assert metrics["total_scored_submissions"] == 310
    assert metrics["semantic_evaluated_count"] == 310
    assert metrics["keyword_evaluated_count"] == 0

    cohort = metrics["cohort_statistics"]
    assert cohort["semantic_mean_score"] == 59.62
    assert cohort["keyword_baseline_mean_score"] is None
    assert cohort["keyword_mean_score"] is None
    assert cohort["score_difference"] is None

    tiers = cohort["performance_tier_distribution"]
    assert tiers["exemplary_or_proficient"] == 130
    assert tiers["developing"] == 78
    assert tiers["unsatisfactory"] == 102


def test_research_metrics_full_scope():
    """
    Task 5 & 8: Verify full-scope semantic mean and whole-database scored submission counts.
    Mean is computed dynamically from the live read-only database to remain accurate
    even as additional records accumulate from ongoing test/development activity.
    """
    response = client.get("/api/v1/dataset/research-metrics?scope=full")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["scope"] == "full"
    n_scored = metrics["total_scored_submissions"]
    assert n_scored >= 333
    assert metrics["semantic_evaluated_count"] >= 333

    cohort = metrics["cohort_statistics"]
    assert cohort["keyword_baseline_mean_score"] is None
    assert cohort["keyword_mean_score"] is None

    # Compute expected mean independently from the same read-only live database
    db = SessionLocal()
    try:
        scored_subs = db.query(StudentSubmission).filter(
            StudentSubmission.status == "scored"
        ).all()
        max_marks_map = {a.id: a.max_marks for a in db.query(Assessment).all()}
        pcts = [
            round(s.total_score / max_marks_map[s.assessment_id] * 100, 4)
            for s in scored_subs
            if s.total_score is not None
            and s.assessment_id in max_marks_map
            and max_marks_map[s.assessment_id] > 0
        ]
        expected_mean = round(sum(pcts) / len(pcts), 2) if pcts else 0.0
    finally:
        db.close()

    assert cohort["semantic_mean_score"] == pytest.approx(expected_mean, abs=0.05), (
        f"Full-scope mean mismatch: API={cohort['semantic_mean_score']}, "
        f"computed={expected_mean} from {len(pcts)} submissions"
    )


def test_default_scope_is_benchmark():
    """
    Task 1: Selector defaults to Java OOP Benchmark Only.
    Endpoints without explicit scope parameter must default to benchmark.
    """
    res_status = client.get("/api/v1/dataset/status")
    assert res_status.status_code == 200
    assert res_status.json()["scope"] == "benchmark"
    assert res_status.json()["assessments_count"] == 5

    res_metrics = client.get("/api/v1/dataset/research-metrics")
    assert res_metrics.status_code == 200
    assert res_metrics.json()["scope"] == "benchmark"
    assert res_metrics.json()["total_scored_submissions"] == 310
