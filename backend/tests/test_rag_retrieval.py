"""
Automated Test Suite for RAG Retrieval Service (Research Component IT23376472).

Tests:
1. CSV parsing and directory path resolution
2. "Criterion Details (JSON)" structured parsing
3. Trust metadata preservation and UNVERIFIED DRAFT reference labeling
4. Retrieval accuracy using Ollama nomic-embed-text (specifically Java class vs object)
5. Retrieval accuracy across all 5 OOP rubric records
6. TF-IDF fallback similarity when Ollama is offline or bypassed
7. Graceful Ollama timeout and connection error handling
8. FastAPI RAG REST endpoints (/retrieve, /documents, /status)
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_retrieval_service import (
    RAGKnowledgeLoader,
    RAGRetrievalService,
    OllamaEmbeddingClient,
    TFIDFFallback,
    resolve_csv_path,
    get_rag_service,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def rag_service():
    """Initializes and returns the RAG service instance."""
    service = RAGRetrievalService()
    service.initialize()
    return service


# ===========================================================================
# 1. CSV Loader & Path Resolution Tests
# ===========================================================================

def test_csv_path_resolution():
    """Verify that the CSV path is correctly resolved to an existing file."""
    path = resolve_csv_path()
    assert os.path.isfile(path), f"Resolved CSV path does not exist: {path}"
    assert "RubriMark_RAG_Lecturer_Rubrics_Draft_v1_1.csv" in path


def test_csv_loader_loads_all_five_records():
    """Verify that all 5 lecturer rubric records (Q1 to Q5) are loaded."""
    docs = RAGKnowledgeLoader.load_from_csv()
    assert len(docs) == 5, f"Expected 5 records, found {len(docs)}"

    q_ids = [d.doc_id for d in docs]
    assert q_ids == ["Q1", "Q2", "Q3", "Q4", "Q5"]


# ===========================================================================
# 2. Criterion Details (JSON) Parsing Tests
# ===========================================================================

def test_criterion_details_json_parsed_properly():
    """Verify that the 'Criterion Details (JSON)' column is accurately parsed."""
    docs = RAGKnowledgeLoader.load_from_csv()
    doc_map = {d.doc_id: d for d in docs}

    # Q1: 4 criteria
    q1 = doc_map["Q1"]
    q1_criteria = q1.metadata["criteria"]
    assert len(q1_criteria) == 4, f"Q1 should have 4 criteria, got {len(q1_criteria)}"

    criterion_names = [c["criterion"] for c in q1_criteria]
    assert "Class definition" in criterion_names
    assert "Object definition" in criterion_names
    assert "Difference between class and object" in criterion_names
    assert "Correct Java example" in criterion_names

    # Check marks sum to 10
    total_marks = sum(c["max_marks"] for c in q1_criteria)
    assert total_marks == 10.0, f"Expected 10 total marks, got {total_marks}"

    # Verify structured fields in each criterion
    for c in q1_criteria:
        assert "criterion" in c
        assert "max_marks" in c
        assert "description" in c
        assert "full_credit" in c
        assert "partial_credit" in c
        assert "zero_credit" in c
        assert len(c["description"]) > 0

    # Q2 to Q5: 3 criteria each
    for qid in ["Q2", "Q3", "Q4", "Q5"]:
        criteria = doc_map[qid].metadata["criteria"]
        assert len(criteria) == 3, f"{qid} should have 3 criteria, got {len(criteria)}"
        assert sum(c["max_marks"] for c in criteria) == 10.0


# ===========================================================================
# 3. Trust Metadata & Unverified Draft Labeling Tests
# ===========================================================================

def test_trust_metadata_and_unverified_draft_marking():
    """
    Verify that Question ID, source file, approval status, and RAG trust level
    are preserved, and that Pending rubrics are clearly marked as unverified draft references.
    """
    docs = RAGKnowledgeLoader.load_from_csv()

    for doc in docs:
        meta = doc.metadata

        # Preserved fields
        assert meta["question_id"] in ["Q1", "Q2", "Q3", "Q4", "Q5"]
        assert "IT23376472_Complete_Lecturer_Rubric_Template" in meta["source_file"]
        assert meta["lecturer_approval"] == "Pending"
        assert meta["rag_trust_level"] == "DRAFT_REFERENCE_ONLY"
        assert meta["rubric_version"] == "draft-v1.1"

        # Explicit verification flag
        assert meta["is_verified"] is False

        # Clear trust label
        assert "[UNVERIFIED DRAFT REFERENCE]" in meta["trust_label"]
        assert "NOT been approved by a lecturer" in meta["trust_label"]

        # Formatted context banner
        formatted = meta["formatted_context"]
        assert "[UNVERIFIED DRAFT REFERENCE - NOT GROUND TRUTH" in formatted
        assert "Approval Status: Pending" in formatted
        assert "Trust Level: DRAFT_REFERENCE_ONLY" in formatted
        assert meta["question"] in formatted
        assert meta["model_answer"] in formatted
        assert meta["learning_outcome"] in formatted
        assert meta["blooms_level"] in formatted


# ===========================================================================
# 4. Retrieval Accuracy Test: Java Class vs Object (Primary Requirement)
# ===========================================================================

def test_retrieval_java_class_vs_object(rag_service):
    """
    Primary Requirement:
    Test the retrieval system using the Java class vs object question.
    Ensure Q1 is the top-ranked match and includes all required context.
    """
    query = "What is the difference between a class and an object in Java? Give a simple example."
    response = rag_service.retrieve(query=query, top_k=3)

    assert response["query"] == query
    assert response["results_returned"] >= 1
    assert len(response["results"]) > 0

    top_result = response["results"][0]
    assert top_result["doc_id"] == "Q1", f"Expected Q1 as top result, got {top_result['doc_id']}"
    assert top_result["similarity_score"] > 0.5, f"Similarity score too low: {top_result['similarity_score']}"

    # Verify all required context fields are present in the top result
    assert "class is a blueprint" in top_result["model_answer"]
    assert "Differentiate Java classes and objects" in top_result["learning_outcome"]
    assert "Understand (L2)" in top_result["blooms_level"]
    assert len(top_result["criteria"]) == 4
    assert "Class definition (2)" in top_result["marking_guide"]
    assert top_result["max_marks"] == "10"
    assert "Accept semantically equivalent" in top_result["lecturer_guidelines"]

    # Verify trust metadata preserved
    assert top_result["question_id"] == "Q1"
    assert "IT23376472_Complete_Lecturer_Rubric_Template" in top_result["source_file"]
    assert top_result["lecturer_approval"] == "Pending"
    assert top_result["rag_trust_level"] == "DRAFT_REFERENCE_ONLY"
    assert top_result["is_verified"] is False
    assert "[UNVERIFIED DRAFT REFERENCE]" in top_result["trust_label"]

    # Verify formatted context and top-level retrieved_context
    assert "[UNVERIFIED DRAFT REFERENCE - NOT GROUND TRUTH - Q1]" in top_result["formatted_context"]
    assert "Question ID: Q1" in response["retrieved_context"]


# ===========================================================================
# 5. Retrieval Accuracy Across All 5 Topics
# ===========================================================================

@pytest.mark.parametrize(
    "query,expected_qid,expected_topic",
    [
        (
            "What is the difference between a class and an object in Java? Give a simple example.",
            "Q1",
            "Classes and Objects",
        ),
        (
            "If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?",
            "Q2",
            "Inheritance",
        ),
        (
            "What happens when a child class overrides a method inherited from its parent class?",
            "Q3",
            "Method Overriding",
        ),
        (
            "Can a static method directly access a non-static variable? Why or why not?",
            "Q4",
            "Static vs Instance Context",
        ),
        (
            "Why is exception handling important in Java?",
            "Q5",
            "Exception Handling",
        ),
    ],
)
def test_retrieval_all_topics_accuracy(rag_service, query, expected_qid, expected_topic):
    """Verify that each of the 5 canonical questions retrieves its matching rubric at rank #1."""
    res = rag_service.retrieve(query=query, top_k=1)
    assert len(res["results"]) == 1
    top = res["results"][0]
    assert top["doc_id"] == expected_qid, f"Expected {expected_qid} for '{query}', got {top['doc_id']}"
    assert top["rag_topic"] == expected_topic


# ===========================================================================
# 6. TF-IDF Fallback Mode Test
# ===========================================================================

def test_tfidf_fallback_retrieval():
    """Verify that the service operates deterministically in TF-IDF fallback mode without Ollama."""
    service = RAGRetrievalService()
    init_res = service.initialize(force_fallback=True)
    assert init_res["embedding_mode"] == "tfidf_fallback"
    assert service.embedding_mode == "tfidf_fallback"

    res = service.retrieve("difference between class and object in Java with example", top_k=2)
    assert res["retrieval_mode"] == "tfidf_fallback"
    assert len(res["results"]) > 0
    assert res["results"][0]["doc_id"] == "Q1"


# ===========================================================================
# 7. Ollama Error & Timeout Handling Tests
# ===========================================================================

def test_ollama_client_unreachable_host_handling():
    """Verify that OllamaEmbeddingClient gracefully handles an unreachable host."""
    client = OllamaEmbeddingClient(
        base_url="http://127.0.0.1:59999",  # unreachable port
        timeout=1.0,
    )
    assert client.check_availability() is False
    assert client.get_embedding("test text") is None


def test_ollama_client_timeout_handling():
    """Verify that OllamaEmbeddingClient gracefully handles timeouts without raising."""
    client = OllamaEmbeddingClient(
        base_url="http://10.255.255.1:11434",  # non-routable IP causes timeout
        timeout=0.001,
    )
    result = client.get_embedding("test timeout")
    assert result is None


# ===========================================================================
# 8. FastAPI RAG Endpoints Tests
# ===========================================================================

def test_api_rag_status_endpoint(client):
    """Test GET /api/v1/rag/status."""
    response = client.get("/api/v1/rag/status")
    assert response.status_code == 200
    data = response.json()
    assert data["initialized"] is True
    assert data["documents_loaded"] == 5
    assert data["ollama_model"] == "nomic-embed-text"
    assert data["embedding_mode"] in ["ollama", "tfidf_fallback"]


def test_api_rag_documents_endpoint(client):
    """Test GET /api/v1/rag/documents lists all 5 records."""
    response = client.get("/api/v1/rag/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 5
    ids = [d["doc_id"] for d in docs]
    assert "Q1" in ids
    assert "Q5" in ids
    # Check that pending records are unverified
    for d in docs:
        assert d["is_verified"] is False
        assert "[UNVERIFIED DRAFT REFERENCE]" in d["trust_label"]


def test_api_rag_get_single_document(client):
    """Test GET /api/v1/rag/documents/Q1."""
    response = client.get("/api/v1/rag/documents/Q1")
    assert response.status_code == 200
    doc = response.json()
    assert doc["question_id"] == "Q1"
    assert doc["rag_topic"] == "Classes and Objects"
    assert len(doc["criteria"]) == 4

    # Test 404 for nonexistent document
    resp_404 = client.get("/api/v1/rag/documents/NONEXISTENT_999")
    assert resp_404.status_code == 404


def test_api_rag_retrieve_endpoint(client):
    """Test POST /api/v1/rag/retrieve with Java class vs object question."""
    payload = {
        "query": "What is the difference between a class and an object in Java? Give a simple example.",
        "top_k": 3,
        "min_similarity": 0.0,
    }
    response = client.post("/api/v1/rag/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == payload["query"]
    assert len(data["results"]) >= 1
    top = data["results"][0]
    assert top["doc_id"] == "Q1"
    assert top["similarity_score"] > 0.0
    assert len(top["criteria"]) == 4
    assert top["is_verified"] is False
    assert "[UNVERIFIED DRAFT REFERENCE]" in top["trust_label"]
    assert "retrieved_context" in data
    assert "Question ID: Q1" in data["retrieved_context"]
