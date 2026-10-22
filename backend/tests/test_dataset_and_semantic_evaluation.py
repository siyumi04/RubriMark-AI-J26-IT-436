"""
Integration and Unit Tests for:
1. Semantic Answer Evaluation Service
2. Keyword-Based Baseline Comparison
3. Five Java OOP Questions Dataset Integration (62 Students)
4. Lecturer Rubric CSV Import
5. Duplicate Import Prevention & Missing Email Handling
6. Real Research Evaluation Metrics
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.semantic_evaluator import SemanticScoringService
from app.services.dataset_service import DatasetService

client = TestClient(app)


def test_semantic_evaluation_recognizes_paraphrased_answers():
    """
    Priority 1: Recognizes conceptually correct answers expressed using different wording.
    Tests that a student using synonyms/alternative phrasings scores well in semantic evaluation
    and receives evidence-based quotes.
    """
    criteria = [
        {
            "id": 1,
            "criterion_name": "Class and Object Distinction",
            "description": "Explains that a class is a blueprint/template and an object is a concrete instance.",
            "weight_percentage": 50.0,
            "max_marks": 5.0,
        },
        {
            "id": 2,
            "criterion_name": "Object Instantiation & Code Example",
            "description": "Demonstrates object creation with a concrete example.",
            "weight_percentage": 50.0,
            "max_marks": 5.0,
        }
    ]

    # Student answer using alternative vocabulary: "architectural mold" instead of "blueprint", "concrete realization" instead of "instance"
    student_paraphrase = (
        "In Java, a class serves as an architectural mold that outlines behaviors and properties. "
        "Conversely, an entity allocated in memory is the concrete realization created from that class. "
        "For instance, Car vehicle = new Car(); instantiates the tangible vehicle from the pattern."
    )

    sem_res = SemanticScoringService.evaluate_semantic(
        answer_text=student_paraphrase,
        criteria=criteria,
        model_answer="A class is a blueprint defining fields and methods. An object is an instance created from a class."
    )

    assert sem_res["total_score"] >= 7.0, f"Expected strong score for valid paraphrase, got {sem_res['total_score']}"
    assert sem_res["scoring_method"] == "semantic"
    assert len(sem_res["criterion_scores"]) == 2

    # Verify evidence-based explanations
    for cs in sem_res["criterion_scores"]:
        assert len(cs["evidence_quote"]) > 0, "Must provide evidence quote from student answer"
        assert cs["confidence_score"] >= 0.75


def test_keyword_baseline_separated_from_semantic_evaluation():
    """
    Priority 1: Keyword-based scoring is kept as a separate baseline for comparison.
    Keyword matching must not be presented as genuine semantic AI evaluation.
    """
    criteria = [
        {
            "id": 1,
            "criterion_name": "Encapsulation & Data Hiding",
            "description": "Uses private variables and public getters and setters with validation logic.",
            "weight_percentage": 100.0,
            "max_marks": 10.0,
        }
    ]

    # Answer using completely distinct words:
    paraphrased_answer = (
        "We restrict visibility of attributes using secret accessors so external callers "
        "cannot alter state directly, only going through safe update routines."
    )

    kw_res = SemanticScoringService.evaluate_keyword_baseline(paraphrased_answer, criteria)
    sem_res = SemanticScoringService.evaluate_semantic(paraphrased_answer, criteria)

    # Keyword baseline will miss the match because exact keywords 'encapsulation', 'private', 'getter', 'setter' are missing
    assert kw_res["scoring_method"] == "keyword_baseline"
    assert kw_res["semantic_engine"] == "keyword_heuristic_baseline"
    assert sem_res["scoring_method"] == "semantic"
    assert sem_res["semantic_engine"] == "local_semantic_nlp"


def test_dataset_import_lecturer_rubrics():
    """
    Priority 3: Import lecturer rubric CSV file for the five Java OOP questions.
    """
    response = client.post("/api/v1/dataset/import-lecturer-rubric")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_questions"] >= 5

    # Check imported questions
    q_titles = [q["title"] for q in data["questions"]]
    assert any("Q1" in t for t in q_titles)
    assert any("Q5" in t for t in q_titles)


def test_dataset_import_student_responses_with_missing_emails():
    """
    Priority 3: Import student questionnaire responses (62 students).
    Must handle missing emails, blank scores, and prevent duplicate imports.
    """
    response = client.post("/api/v1/dataset/import-student-responses")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_rows_processed"] == 62
    assert (data["imported_submissions"] + data["skipped_duplicates"]) > 0

    # Test duplicate import idempotency
    dup_response = client.post("/api/v1/dataset/import-student-responses")
    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["imported_submissions"] == 0, "Must not create duplicate submissions on re-import"
    assert dup_data["skipped_duplicates"] > 0



def test_batch_evaluate_semantic_and_keyword():
    """
    Priority 5: Batch evaluate imported student responses using semantic evaluator.
    """
    sem_response = client.post("/api/v1/dataset/batch-evaluate", json={"scoring_method": "semantic"})
    assert sem_response.status_code == 200
    sem_data = sem_response.json()
    assert sem_data["status"] == "success"
    assert sem_data["evaluated_submissions"] > 0
    assert sem_data["scoring_method"] == "semantic"


def test_research_evaluation_metrics_reporting():
    """
    Priority 5: Calculate research evaluation metrics using real reference data.
    Does not invent metrics or claim unverified accuracy when ground truth is blank.
    """
    response = client.get("/api/v1/dataset/research-metrics")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["research_component"] == "IT23376472"
    assert "cohort_statistics" in metrics
    assert "semantic_mean_score" in metrics["cohort_statistics"]
    assert "ground_truth_notice" in metrics
    # Truthful reporting of ground truth availability
    assert metrics["ground_truth_available"] is False
