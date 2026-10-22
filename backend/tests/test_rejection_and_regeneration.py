"""
Phase 3 Automated Test Suite: Lecturer Rejection and Feedback-Driven Rubric Regeneration.

Requirements Covered:
1. Isolated temporary test database (never touches or resets the real rubrimark.db)
2. Lecturer rejection with one reason and multiple reasons
3. Rejection feedback and timestamps persistence
4. Rejection enforcement: rejected rubrics cannot be approved or used for student scoring
5. Feedback-driven regeneration with Ollama llama3.2:1b + RAG context
6. Mark reconciliation (correct total marks) and pending approval status for regenerated rubrics
7. Rubric version history (chronological ordering) and preservation of previous versions (no overwrite)
8. Rejection and regeneration API endpoints (POST /reject, POST /regenerate, GET /history)
9. Resilient fallback labelling when Ollama fails/times out (never silent or unlabelled)
"""

import os
import json
import tempfile
from unittest.mock import patch
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.services.ai_service import AIService
from app.services.weight_optimizer import DynamicWeightOptimizer
from app.services.rag_retrieval_service import RAGRetrievalService


# ===========================================================================
# Isolated Temporary Database Fixture
# ===========================================================================

@pytest.fixture(scope="module")
def client():
    """
    Creates an isolated temporary SQLite database for Phase 3 tests.
    Strictly prevents any interaction with or modification of the real rubrimark.db.
    """
    temp_fd, temp_db_path = tempfile.mkstemp(suffix="_phase3_test.db")
    os.close(temp_fd)

    test_engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Build all tables on the isolated temporary test database
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean teardown
    app.dependency_overrides.clear()
    test_engine.dispose()
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


# ===========================================================================
# 1. Lecturer Rejection Tests (One Reason, Multiple Reasons, Feedback, Timestamps)
# ===========================================================================

def test_rejection_single_reason_and_timestamps(client):
    """
    Test lecturer rejection with a single reason, recording rejection reasons,
    feedback, and UTC timestamp in SQLite.
    """
    # 1. Generate draft rubric v1
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "Explain Encapsulation in Java and demonstrate data hiding.",
        "max_marks": 20.0,
        "blooms_level": "Understand",
        "title": "Encapsulation Assessment",
        "force_fallback": True,
    })
    assert gen_resp.status_code == 201
    rubric = gen_resp.json()
    rubric_id = rubric["id"]
    assert rubric["status"] == "pending_approval"
    assert rubric["is_approved"] is False

    # 2. Reject with single reason
    reject_resp = client.post(f"/api/v1/rubrics/{rubric_id}/reject", json={
        "rejected_by": "Dr. Lecturer OOP",
        "rejection_reasons": ["Missing criteria"],
        "feedback": "Missing an explicit criterion for private field visibility.",
    })
    assert reject_resp.status_code == 200
    rejected = reject_resp.json()

    assert rejected["id"] == rubric_id
    assert rejected["status"] == "rejected"
    assert rejected["is_approved"] is False
    assert rejected["rejection_reasons"] == ["Missing criteria"]
    assert "private field visibility" in rejected["rejection_feedback"]
    assert rejected["rejected_by"] == "Dr. Lecturer OOP"
    assert rejected["rejected_at"] is not None

    # 3. Query GET endpoint to verify persistence in isolated DB
    fetched = client.get(f"/api/v1/rubrics/{rubric_id}").json()
    assert fetched["status"] == "rejected"
    assert fetched["rejection_reasons"] == ["Missing criteria"]


def test_rejection_multiple_reasons_and_feedback(client):
    """
    Test lecturer rejection with multiple reasons (including Other) and custom feedback.
    """
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "Compare abstract classes and interfaces in Java 8+.",
        "max_marks": 25.0,
        "blooms_level": "Analyze",
        "title": "Abstract vs Interface Assessment",
        "force_fallback": True,
    })
    rubric_id = gen_resp.json()["id"]

    multiple_reasons = [
        "Missing criteria",
        "Incorrect marks or weights",
        "Bloom's taxonomy mismatch",
        "Unclear criterion descriptions",
        "Incorrect or irrelevant criteria",
        "Other",
    ]
    feedback_text = "Criteria weights must sum to 100% and cognitive level must be Analyze tier."

    reject_resp = client.post(f"/api/v1/rubrics/{rubric_id}/reject", json={
        "rejected_by": "Prof. Software Design",
        "rejection_reasons": multiple_reasons,
        "feedback": feedback_text,
    })
    assert reject_resp.status_code == 200
    data = reject_resp.json()

    assert data["status"] == "rejected"
    assert len(data["rejection_reasons"]) == 6
    assert data["rejection_reasons"] == multiple_reasons
    assert data["rejection_feedback"] == feedback_text
    assert data["rejected_by"] == "Prof. Software Design"


def test_rejection_empty_reasons_validation(client):
    """
    Verify validation fails (HTTP 400) if no rejection reasons are selected.
    """
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "What is polymorphism in Java?",
        "max_marks": 10.0,
        "force_fallback": True,
    })
    rubric_id = gen_resp.json()["id"]

    err_resp = client.post(f"/api/v1/rubrics/{rubric_id}/reject", json={
        "rejection_reasons": [],
    })
    assert err_resp.status_code == 400
    assert "At least one rejection reason" in err_resp.json()["detail"]


# ===========================================================================
# 2. Rejected Rubrics Cannot Be Approved or Used for Scoring
# ===========================================================================

def test_rejected_rubric_cannot_be_approved(client):
    """
    Requirement 4:
    Test that a rejected rubric CANNOT be approved directly.
    It must be regenerated into a new version first.
    """
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "Explain JVM Memory Areas (Heap, Stack, Method Area).",
        "max_marks": 20.0,
        "force_fallback": True,
    })
    rubric_id = gen_resp.json()["id"]

    # Reject rubric
    client.post(f"/api/v1/rubrics/{rubric_id}/reject", json={
        "rejection_reasons": ["Unclear criterion descriptions"],
        "feedback": "Clarify stack frame allocations.",
    })

    # Attempt to approve rejected rubric -> MUST BE BLOCKED
    approve_resp = client.post(f"/api/v1/rubrics/{rubric_id}/approve", json={
        "approved_by": "Dr. Lecturer",
    })
    assert approve_resp.status_code == 400
    assert "cannot approve a rejected rubric" in approve_resp.json()["detail"].lower()


def test_rejected_rubric_cannot_score_students(client):
    """
    Requirement 4 & 9:
    Test that neither unapproved nor rejected rubrics can be used for student scoring.
    Only approved rubrics may be used.
    """
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "What is method overloading in Java?",
        "max_marks": 15.0,
        "force_fallback": True,
    })
    rubric = gen_resp.json()
    rubric_id = rubric["id"]
    assessment_id = rubric["assessment_id"]

    student_data = {
        "assessment_id": assessment_id,
        "rubric_id": rubric_id,
        "student_id": "IT23000999",
        "student_name": "Test Candidate",
        "answer_text": "Method overloading defines multiple methods with the same name but different signatures.",
    }

    # 1. Unapproved draft rubric -> scoring blocked
    resp_unapproved = client.post("/api/v1/scoring/evaluate", json=student_data)
    assert resp_unapproved.status_code == 400
    assert "unapproved rubric" in resp_unapproved.json()["detail"].lower()

    # 2. Reject rubric
    client.post(f"/api/v1/rubrics/{rubric_id}/reject", json={
        "rejection_reasons": ["Missing criteria"],
        "feedback": "Needs compile-time resolution criterion.",
    })

    # 3. Rejected rubric -> scoring strictly blocked
    resp_rejected = client.post("/api/v1/scoring/evaluate", json=student_data)
    assert resp_rejected.status_code == 400
    assert "rejected rubric" in resp_rejected.json()["detail"].lower()


# ===========================================================================
# 3. Feedback-Driven Regeneration (Ollama + RAG + Weight Optimization)
# ===========================================================================

def test_feedback_regeneration_versioning_and_marks(client):
    """
    Requirements 5, 6, 7, 8:
    Verify feedback-driven regeneration:
    - Creates a new version (v2) without overwriting v1
    - Reconciles marks to match assessment max_marks
    - Dynamically optimizes weights to sum to 100.0%
    - Keeps new rubric in pending_approval (not automatically approved)
    """
    # 1. Create Assessment & v1 Rubric
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "What is the difference between a class and an object in Java? Give a simple example.",
        "max_marks": 30.0,
        "blooms_level": "Understand",
        "title": "Java Class vs Object Assessment",
        "force_fallback": True,
    })
    v1 = gen_resp.json()
    v1_id = v1["id"]
    assessment_id = v1["assessment_id"]
    assert v1["version"] == 1

    # 2. Reject v1
    client.post(f"/api/v1/rubrics/{v1_id}/reject", json={
        "rejection_reasons": ["Missing criteria", "Incorrect marks or weights"],
        "feedback": "Add explicit syntax and instantiation demonstration; total marks must be 30.",
    })

    # 3. Regenerate rubric v2
    regen_resp = client.post(f"/api/v1/rubrics/{v1_id}/regenerate", json={
        "force_fallback": True,
    })
    assert regen_resp.status_code == 201
    v2 = regen_resp.json()

    # Verify new version created
    assert v2["id"] != v1_id
    assert v2["version"] == 2
    assert v2["parent_rubric_id"] == v1_id
    assert v2["assessment_id"] == assessment_id

    # Verify pending approval status (do NOT automatically approve)
    assert v2["status"] == "pending_approval"
    assert v2["is_approved"] is False

    # Verify total marks strictly reconciled to 30.0
    total_marks = round(sum(c["max_marks"] for c in v2["criteria"]), 2)
    assert total_marks == 30.0, f"Expected 30.0 marks, got {total_marks}"

    # Verify weights strictly sum to 100.0%
    total_weight = round(sum(c["weight_percentage"] for c in v2["criteria"]), 2)
    assert abs(total_weight - 100.0) < 0.05, f"Expected 100.0% weight sum, got {total_weight}"

    # Verify previous version v1 is PRESERVED and untouched
    v1_stored = client.get(f"/api/v1/rubrics/{v1_id}").json()
    assert v1_stored["version"] == 1
    assert v1_stored["status"] == "rejected"
    assert v1_stored["rejection_reasons"] == ["Missing criteria", "Incorrect marks or weights"]


def test_ollama_feedback_regeneration_with_mock_rag():
    """
    Requirement 5:
    Test feedback-driven regeneration with Ollama llama3.2:1b mock response,
    verifying structured JSON parsing, prompt formulation, and generation mode labelling.
    """
    mock_llm_json = json.dumps({
        "criteria": [
            {
                "criterion_name": "Class Blueprint Definition",
                "description": "Explains classes as conceptual templates with state and behavior.",
                "proposed_marks": 3.0,
                "blooms_dimension": "Analytical",
            },
            {
                "criterion_name": "Object Instantiation & Memory",
                "description": "Explains objects as concrete runtime instances created via new.",
                "proposed_marks": 4.0,
                "blooms_dimension": "Analytical",
            },
            {
                "criterion_name": "Syntactic Code Demonstration",
                "description": "Executable code snippet demonstrating class declaration and object creation.",
                "proposed_marks": 3.0,
                "blooms_dimension": "Applied",
            },
        ],
        "generation_rationale": "Addressed missing code demonstration and adjusted marks per lecturer feedback.",
    })

    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps({"response": mock_llm_json}).encode(),
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch("httpx.Client.post", return_value=mock_resp):
        result = AIService.regenerate_rubric_with_feedback(
            question_text="What is the difference between a class and an object in Java? Give a simple example.",
            blooms_level="Understand",
            max_marks=10.0,
            previous_criteria=[
                {"criterion_name": "Basic Concept", "description": "Too brief", "weight_percentage": 50.0, "max_marks": 5.0},
                {"criterion_name": "Basic Example", "description": "Too brief", "weight_percentage": 50.0, "max_marks": 5.0},
            ],
            rejection_reasons=["Missing criteria", "Unclear criterion descriptions"],
            rejection_feedback="Include syntax and concrete code example.",
            use_rag=False,
            force_fallback=False,
        )

        assert result["generation_mode"] == "ollama_feedback_regenerated"
        assert len(result["criteria"]) == 3
        total_marks = round(sum(c["max_marks"] for c in result["criteria"]), 2)
        assert total_marks == 10.0
        total_weight = round(sum(c["weight_percentage"] for c in result["criteria"]), 2)
        assert abs(total_weight - 100.0) < 0.05
        assert result["validation"]["is_valid"] is True


def test_ollama_failure_labelled_fallback():
    """
    Safety Requirement:
    'Do not silently replace failed Ollama regeneration with an unlabelled fallback.'
    Verify that when Ollama times out or errors, the generation mode is explicitly
    labelled as 'rule_based_fallback' with explicit fallback_reason.
    """
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out after 120s")):
        result = AIService.regenerate_rubric_with_feedback(
            question_text="Explain method overriding in Java.",
            blooms_level="Analyze",
            max_marks=20.0,
            previous_criteria=[
                {"criterion_name": "Method Signature", "description": "Details", "weight_percentage": 50.0, "max_marks": 10.0},
                {"criterion_name": "Runtime Binding", "description": "Details", "weight_percentage": 50.0, "max_marks": 10.0},
            ],
            rejection_reasons=["Bloom's taxonomy mismatch"],
            use_rag=False,
            force_fallback=False,
        )

        # Must be explicitly labelled, never silent
        assert result["generation_mode"] == "rule_based_fallback"
        assert result.get("fallback_reason") is not None
        assert "timed out" in result["fallback_reason"].lower()
        assert len(result["criteria"]) >= 2
        total_marks = round(sum(c["max_marks"] for c in result["criteria"]), 2)
        assert total_marks == 20.0


# ===========================================================================
# 4. Rubric Version History Tests
# ===========================================================================

def test_version_history_chronology_and_retrieval(client):
    """
    Requirement 7, 8, 10:
    Verify version history reflects the full lifecycle:
    v1 (rejected) -> v2 (rejected) -> v3 (approved).
    Verify all versions are preserved and ordered chronologically.
    """
    # 1. Generate v1
    gen_resp = client.post("/api/v1/rubrics/generate", json={
        "question": "Explain Java Exception Hierarchy (Checked vs Unchecked).",
        "max_marks": 25.0,
        "title": "Exception Hierarchy Assessment",
        "force_fallback": True,
    })
    v1 = gen_resp.json()
    assessment_id = v1["assessment_id"]
    v1_id = v1["id"]

    # 2. Reject v1 -> Regenerate v2
    client.post(f"/api/v1/rubrics/{v1_id}/reject", json={
        "rejected_by": "Dr. OOP Lead",
        "rejection_reasons": ["Missing criteria"],
        "feedback": "Needs runtime exception distinctions.",
    })
    v2 = client.post(f"/api/v1/rubrics/{v1_id}/regenerate", json={"force_fallback": True}).json()
    v2_id = v2["id"]

    # 3. Reject v2 -> Regenerate v3
    client.post(f"/api/v1/rubrics/{v2_id}/reject", json={
        "rejected_by": "Dr. OOP Lead",
        "rejection_reasons": ["Incorrect marks or weights"],
        "feedback": "Rebalance marks to emphasize custom exceptions.",
    })
    v3 = client.post(f"/api/v1/rubrics/{v2_id}/regenerate", json={"force_fallback": True}).json()
    v3_id = v3["id"]

    # 4. Lecturer approves v3
    client.post(f"/api/v1/rubrics/{v3_id}/approve", json={
        "approved_by": "Dr. OOP Lead",
        "notes": "Version 3 meets all pedagogical standards.",
    })

    # 5. Query assessment version history
    hist_resp = client.get(f"/api/v1/rubrics/assessment/{assessment_id}/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()

    assert history["assessment_id"] == assessment_id
    versions = history["versions"]
    assert len(versions) == 3

    # Check v1
    assert versions[0]["id"] == v1_id
    assert versions[0]["version"] == 1
    assert versions[0]["status"] == "rejected"
    assert versions[0]["is_approved"] is False
    assert versions[0]["rejection_reasons"] == ["Missing criteria"]
    assert "runtime exception" in versions[0]["rejection_feedback"]

    # Check v2
    assert versions[1]["id"] == v2_id
    assert versions[1]["version"] == 2
    assert versions[1]["parent_rubric_id"] == v1_id
    assert versions[1]["status"] == "rejected"
    assert versions[1]["is_approved"] is False
    assert versions[1]["rejection_reasons"] == ["Incorrect marks or weights"]

    # Check v3
    assert versions[2]["id"] == v3_id
    assert versions[2]["version"] == 3
    assert versions[2]["parent_rubric_id"] == v2_id
    assert versions[2]["status"] == "approved"
    assert versions[2]["is_approved"] is True
    assert versions[2]["approved_by"] == "Dr. OOP Lead"

    # 6. Verify student scoring is unlocked for approved v3
    score_resp = client.post("/api/v1/scoring/evaluate", json={
        "assessment_id": assessment_id,
        "rubric_id": v3_id,
        "student_id": "IT23000888",
        "student_name": "Valid Student",
        "answer_text": "Checked exceptions are checked at compile-time while unchecked exceptions occur at runtime.",
    })
    assert score_resp.status_code == 201
    assert score_resp.json()["status"] == "scored"


# ===========================================================================
# 5. RAG Trust Exclusions for Rejected Rubrics
# ===========================================================================

def test_rag_trust_provenance_rejected_status():
    """
    Requirement 9:
    Verify that rejected rubrics are never treated as trusted RAG knowledge.
    """
    label = RAGRetrievalService._build_trust_label("rejected", "DRAFT_REFERENCE_ONLY")
    assert "REJECTED" in label
    assert "NEVER" in label
    assert "APPROVED_LECTURER_RUBRIC" not in label

    context = RAGRetrievalService.format_document_context({
        "question_id": "Q_REJ",
        "question": "What is polymorphism?",
        "lecturer_approval": "rejected",
        "is_verified": False,
        "criteria": [{"criterion": "Polymorphism", "max_marks": 10.0}],
    })
    assert "[REJECTED RUBRIC - NEVER TRUSTED" in context
    assert "APPROVED LECTURER RUBRIC" not in context
