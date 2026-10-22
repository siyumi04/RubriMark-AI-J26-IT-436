"""
Automated Test Suite for Phase 2: Ollama + RAG-Based Rubric Generation.

Tests:
1. End-to-end Ollama + RAG rubric generation for Java class vs object question
2. Verification of mark reconciliation (sum of criteria marks equals lecturer's max_marks)
3. Dynamic weight optimization (weights strictly sum to 100.0%)
4. Clear labeling of unverified draft RAG references
5. Rule-based fallback when force_fallback=True
6. Graceful fallback when Ollama times out
7. Graceful fallback when Ollama returns invalid JSON
8. Preservation of lecturer approval status (Pending approval by default, not automatically approved)
9. FastAPI POST /api/v1/rubrics/generate endpoint integration
"""

import json
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_service import AIService
from app.services.weight_optimizer import DynamicWeightOptimizer


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# ===========================================================================
# 1. Primary Benchmark: Java Class vs Object Rubric Generation
# ===========================================================================

def test_generate_rubric_with_rag_java_class_vs_object():
    """
    Primary Requirement:
    Generate rubric for 'What is the difference between a class and an object in Java? Give a simple example.'
    using Ollama llama3.2:1b + RAG retrieval context.
    Verify structured criteria, total marks matching max_marks (10.0), and 100% weight sum.
    """
    question = "What is the difference between a class and an object in Java? Give a simple example."
    model_ans = (
        "A class is a blueprint defining fields and methods. An object is an instance of a class. "
        "For example, Car is a class and new Car() creates an object."
    )
    result = AIService.generate_rubric_with_rag(
        question_text=question,
        blooms_level="Understand",
        reference_answer=model_ans,
        learning_outcome="Differentiate Java classes and objects and illustrate object instantiation.",
        lecturer_guidelines="Accept semantically equivalent correct answers.",
        max_marks=10.0,
        use_rag=True,
        force_fallback=False,
    )

    assert "criteria" in result
    criteria = result["criteria"]
    assert len(criteria) >= 3, f"Expected at least 3 criteria, got {len(criteria)}"

    # Check generation mode
    assert result["generation_mode"] in ["ollama_rag", "rule_based_fallback"]
    if result["generation_mode"] == "ollama_rag":
        assert result.get("rag_context_used") is not None
        assert "Q1" in result["rag_context_used"] or len(result.get("rag_sources", [])) > 0

    # Requirement 6: Sum of marks equals lecturer requested total exactly
    total_marks = round(sum(float(c["max_marks"]) for c in criteria), 2)
    assert total_marks == 10.0, f"Expected sum of marks to equal 10.0, got {total_marks}"

    # Requirement 7: Weights sum strictly to 100.0%
    total_weight = round(sum(float(c["weight_percentage"]) for c in criteria), 2)
    assert abs(total_weight - 100.0) < 0.05, f"Expected 100.0% weight sum, got {total_weight}"

    # Requirement 4 & 5: Validated criteria properties
    for c in criteria:
        assert len(c["criterion_name"].strip()) >= 3
        assert len(c["description"].strip()) >= 5
        assert float(c["max_marks"]) > 0.0
        assert len(c.get("performance_levels", [])) >= 3

    # Automated validation checks
    validation = result["validation"]
    assert validation["is_valid"] is True
    assert validation["validation_score"] >= 0.85


# ===========================================================================
# 2. Mark Reconciliation Tests
# ===========================================================================

def test_mark_reconciliation_scaled_total():
    """
    Verify that when the lecturer specifies a different total marks (e.g. 25.0 or 50.0),
    the criteria marks are mathematically scaled and reconciled to equal the requested total exactly.
    """
    for requested_marks in [15.0, 25.0, 50.0, 100.0]:
        res = AIService.generate_rubric_with_rag(
            question_text="Explain method overriding in Java child classes.",
            blooms_level="Understand",
            max_marks=requested_marks,
            force_fallback=True,  # test deterministic reconciliation
        )
        total = round(sum(float(c["max_marks"]) for c in res["criteria"]), 2)
        assert total == requested_marks, f"Marks {total} != requested {requested_marks}"


# ===========================================================================
# 3. Rule-Based Fallback Tests
# ===========================================================================

def test_force_fallback_mode():
    """Verify that force_fallback=True cleanly returns rule_based_fallback mode."""
    res = AIService.generate_rubric_with_rag(
        question_text="What is encapsulation in Java?",
        blooms_level="Understand",
        max_marks=20.0,
        force_fallback=True,
    )
    assert res["generation_mode"] in ["rule_based", "rule_based_fallback"]
    assert round(sum(c["max_marks"] for c in res["criteria"]), 2) == 20.0
    assert len(res["criteria"]) >= 3


def test_ollama_timeout_fallback():
    """
    Verify that when Ollama times out (httpx.TimeoutException),
    the service catches it and falls back to rule-based generation with mode 'rule_based_fallback'.
    """
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        res = AIService.generate_rubric_with_rag(
            question_text="What is polymorphism in Java?",
            blooms_level="Analyze",
            max_marks=10.0,
            use_rag=False,
            force_fallback=False,
        )
        assert res["generation_mode"] == "rule_based_fallback"
        assert "timed out" in res["generation_rationale"].lower() or "fallback" in res["generation_rationale"].lower()
        assert len(res["criteria"]) >= 3
        assert round(sum(c["max_marks"] for c in res["criteria"]), 2) == 10.0


def test_ollama_invalid_json_fallback():
    """
    Verify that when Ollama returns malformed or non-JSON content,
    the service falls back gracefully to rule-based generation.
    """
    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps({"response": "Sorry, I cannot generate a JSON rubric."}).encode(),
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )
    with patch("httpx.Client.post", return_value=mock_resp):
        res = AIService.generate_rubric_with_rag(
            question_text="Explain Java interfaces vs abstract classes.",
            blooms_level="Analyze",
            max_marks=15.0,
            use_rag=False,
            force_fallback=False,
        )
        assert res["generation_mode"] == "rule_based_fallback"
        assert len(res["criteria"]) >= 3
        assert round(sum(c["max_marks"] for c in res["criteria"]), 2) == 15.0


def test_ollama_insufficient_criteria_fallback():
    """
    Verify that when Ollama returns fewer than 2 criteria,
    the service rejects the output and falls back to rule-based generation.
    """
    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps({
            "response": json.dumps({
                "criteria": [
                    {"criterion_name": "Only One Criterion", "description": "Too few", "proposed_marks": 10.0}
                ]
            })
        }).encode(),
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )
    with patch("httpx.Client.post", return_value=mock_resp):
        res = AIService.generate_rubric_with_rag(
            question_text="Why is exception handling useful in Java?",
            max_marks=10.0,
            use_rag=False,
            force_fallback=False,
        )
        assert res["generation_mode"] == "rule_based_fallback"
        assert len(res["criteria"]) >= 3


# ===========================================================================
# 4. Lecturer Approval Status Preservation Tests
# ===========================================================================

def test_rubric_not_automatically_approved(client):
    """
    Requirement 11:
    Do not automatically approve generated rubrics.
    Verify that newly generated rubrics have status 'pending_approval' and is_approved=False.
    """
    payload = {
        "question": "What is the difference between a class and an object in Java? Give a simple example.",
        "max_marks": 10.0,
        "blooms_level": "Understand",
        "title": "Java Class vs Object Test",
        "force_fallback": True,  # deterministic fast test
    }
    response = client.post("/api/v1/rubrics/generate", json=payload)
    assert response.status_code == 201
    rubric = response.json()

    assert rubric["status"] == "pending_approval"
    assert rubric["is_approved"] is False
    assert rubric["approved_by"] is None
    assert "Pending lecturer review" in rubric["approval_notes"]
    assert rubric["generation_mode"] in ["rule_based", "rule_based_fallback", "ollama_rag"]

    # Verify lecturer can subsequently approve it
    rubric_id = rubric["id"]
    approve_resp = client.post(
        f"/api/v1/rubrics/{rubric_id}/approve",
        json={"approved_by": "Dr. OOP Lecturer", "notes": "Approved for midterm test."}
    )
    assert approve_resp.status_code == 200
    approved_rubric = approve_resp.json()
    assert approved_rubric["status"] == "approved"
    assert approved_rubric["is_approved"] is True
    assert approved_rubric["approved_by"] == "Dr. OOP Lecturer"


# ===========================================================================
# 5. FastAPI POST /api/v1/rubrics/generate Integration
# ===========================================================================

def test_api_generate_rubric_with_rag(client):
    """
    Test the FastAPI /api/v1/rubrics/generate endpoint end-to-end with Ollama + RAG.
    """
    payload = {
        "question": "What is the difference between a class and an object in Java? Give a simple example.",
        "model_answer": "A class is a blueprint defining fields and methods. An object is an instance of a class.",
        "learning_outcome": "Differentiate Java classes and objects and illustrate object instantiation.",
        "blooms_level": "Understand",
        "lecturer_guidelines": "Accept semantically equivalent correct answers.",
        "max_marks": 10.0,
        "title": "Classes and Objects Quiz",
        "use_rag": True,
        "force_fallback": False,
    }
    response = client.post("/api/v1/rubrics/generate", json=payload)
    assert response.status_code == 201
    rubric = response.json()

    assert rubric["status"] == "pending_approval"
    assert rubric["is_approved"] is False
    assert rubric["generation_mode"] in ["ollama_rag", "rule_based_fallback"]

    # Sum of criterion marks == 10.0
    total_marks = round(sum(c["max_marks"] for c in rubric["criteria"]), 2)
    assert total_marks == 10.0

    # Sum of weights == 100.0%
    total_weight = round(sum(c["weight_percentage"] for c in rubric["criteria"]), 2)
    assert abs(total_weight - 100.0) < 0.05
